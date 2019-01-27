import ctypes
import inspect
import threading
import time
import json
import serial
import textwrap
from emp_wsb.wsServer import WebsocketServer

BUFFER_SIZE = 1024


class RawReplError(BaseException):
    pass


class RawRepl:
    def __init__(self, device, baudrate=115200, rawdelay=0):
        self._rawdelay = rawdelay
        self._repl = serial.Serial(device, baudrate)

    def read_until(self, min_num_bytes, ending, timeout=10, data_consumer=None):
        data = self._repl.read(min_num_bytes)
        if data_consumer:
            data_consumer(data)
        timeout_count = 0
        while True:
            if data.endswith(ending):
                break
            elif self._repl.inWaiting() > 0:
                new_data = self._repl.read(1)
                data = data + new_data
                if data_consumer:
                    data_consumer(new_data)
                timeout_count = 0
            else:
                timeout_count += 1
                if timeout is not None and timeout_count >= 100 * timeout:
                    break
                time.sleep(0.01)
        return data

    def enter_raw_repl(self):
        if not self._enter_rawrepl:
            print('==> Entering Raw REPL')
            self._enter_rawrepl = True

            # Brief delay before sending RAW MODE char if requests
            if self._rawdelay > 0:
                time.sleep(self._rawdelay)

            # ctrl-C twice: interrupt any running program
            self._repl.write(b'\r\x03\x03')

            # flush input (without relying on serial.flushInput())
            n = self._repl.inWaiting()
            while n > 0:
                self._repl.read(n)
                n = self._repl.inWaiting()
            time.sleep(2)

            self._repl.write(b'\r\x01')  # ctrl-A: enter raw REPL
            data = self.read_until(1, b'raw REPL; CTRL-B to exit\r\n>')
            if not data.endswith(b'raw REPL; CTRL-B to exit\r\n>'):
                print(data)
                raise RawReplError('could not enter raw repl')
            print('---> now in rawrepl mode')

    def exit_raw_repl(self):
        if self._enter_rawrepl:
            print('==> Exit Raw REPL')
            self._enter_rawrepl = False
            self._repl.write(b'\r\x02')  # ctrl-B: enter friendly REPL

    def follow(self, timeout, data_consumer=None):
        # wait for normal output
        data = self.read_until(1, b'\x04', timeout=timeout,
                               data_consumer=data_consumer)
        if not data.endswith(b'\x04'):
            raise RawReplError('timeout waiting for first EOF reception')
        data = data[:-1]

        # wait for error output
        data_err = self.read_until(1, b'\x04', timeout=timeout)
        if not data_err.endswith(b'\x04'):
            raise RawReplError('timeout waiting for second EOF reception')
        data_err = data_err[:-1]

        # return normal and error output
        return data, data_err

    def exec_raw_no_follow(self, command):
        if isinstance(command, bytes):
            command_bytes = command
        else:
            command_bytes = bytes(command, encoding='utf8')

        # check we have a prompt
        # data = self.read_until(1, b'>')
        # if not data.endswith(b'>'):
        #     raise RawReplError('could not enter raw repl')

        # write command
        for i in range(0, len(command_bytes), 256):
            self._repl.write(
                command_bytes[i:min(i + 256, len(command_bytes))])
            time.sleep(0.01)
        self._repl.write(b'\x04')

        # check if we could exec command
        # data = self._repl.read(2)
        # if data != b'OK':
        #     raise RawReplError('could not exec command')

    def exec_raw(self, command, timeout=10, data_consumer=None):
        self.exec_raw_no_follow(command)
        return self.follow(timeout, data_consumer)

    def eval(self, expression):
        ret = self.exec_('print({})'.format(expression))
        ret = ret.strip()
        return ret

    def exec_(self, command):
        ret, ret_err = self.exec_raw(command)
        if ret_err:
            raise RawReplError('exception', ret, ret_err)
        return ret

    def execfile(self, filename):
        with open(filename, 'rb') as f:
            pyfile = f.read()
        return self.exec_(pyfile)

    def get_file(self, filename):
        """Retrieve the contents of the specified file and return its contents
        as a byte string.
        """
        # Open the file and read it a few bytes at a time and print out the
        # raw bytes.  Be careful not to overload the UART buffer so only write
        # a few bytes at a time, and don't use print since it adds newlines and
        # expects string data.
        command = """
                import sys
                with open('{0}', 'rb') as infile:
                    while True:
                        result = infile.read({1})
                        if result == b'':
                            break
                        len = sys.stdout.write(result)
            """.format(
            filename, BUFFER_SIZE
        )
        self.enter_raw_repl()
        try:
            out = self.exec_(textwrap.dedent(command))
        except RawReplError as ex:
            # Check if this is an OSError #2, i.e. file doesn't exist and
            # rethrow it as something more descriptive.
            if ex.args[2].decode("utf-8").find("OSError: [Errno 2] ENOENT") != -1:
                raise RuntimeError("No such file: {0}".format(filename))
            else:
                raise ex
        self.exit_raw_repl()
        return out[2::]

    def put_file(self, filename, data):
        """Create or update the specified file with the provided data.
        """

        data = data.encode('utf-8')
        # Open the file for writing on the board and write chunks of data.
        # self.enter_raw_repl()
        self.exec_("f = open('{0}', 'wb')".format(filename))
        size = len(data)
        # Loop through and write a buffer size chunk of data at a time.
        for i in range(0, size, BUFFER_SIZE):
            chunk_size = min(BUFFER_SIZE, size - i)
            chunk = repr(data[i: i + chunk_size])
            # Make sure to send explicit byte strings (handles python 2 compatibility).
            if not chunk.startswith("b"):
                chunk = "b" + chunk
            self.exec_("f.write({0})".format(chunk))
        self.exec_("f.close()")
        self.exit_raw_repl()


class WSB(RawRepl):
    def __init__(self, device, baudrate=115200, port=9000, rawdelay=0):
        super().__init__(device, baudrate=baudrate, rawdelay=rawdelay)
        # self._rawdelay = rawdelay
        # self._repl = serial.Serial(device, baudrate)
        self._server = WebsocketServer(port)
        self._server.set_fn_new_client(self._new_client)
        self._server.set_fn_client_left(self._client_left)
        self._server.set_fn_message_received(self._message_received)
        self._timer = None
        self._forward_job = None
        self._enter_rawrepl = False

    def _new_client(self, client, server):
        print("==> EMP-IDE Connected!")

    def _client_left(self, client, server):
        print("==> EMP-IDE Disconnected!")

    def _message_received(self, client, server, message):
        print("--> Message received: %s" % message)

        if message == 'EnterRawRepl':
            self.enter_raw_repl()
        elif message == 'ExitRawRepl':
            self.exit_raw_repl()
        elif message.startswith('{"put":'):
            message = message.replace('\n', r'\n')
            pdu = eval(message)
            filename = pdu['put']
            data = pdu['data']
            # print(data)
            self.put_file(filename, data)
        elif message.startswith('{"get":'):
            pdu = eval(message)
            filename = pdu['get']
            data = {"func": 'get_code',
                    "data": {
                        "filename": filename,
                        "code": self.get_file(filename).decode('utf-8')
                    }
                    }

            self._server.send_message(
                WebsocketServer.clients[0], json.dumps(data))
        else:
            self._repl.write(message.encode('utf-8'))

    # 转发函数
    def _forward(self, server):
        def poll():
            if WebsocketServer.clients:
                data = None
                if not self._enter_rawrepl:
                    data = self._repl.read().decode('utf-8', errors='ignore')

                try:
                    if data:
                        server.send_message(WebsocketServer.clients[0], data)
                except:
                    pass

            self._timer = threading.Timer(0.00001, poll)
            self._timer.start()

        self._timer = threading.Timer(0.00001, poll)
        self._timer.start()

    def start(self):
        fjob = threading.Thread(target=self._forward, args=(self._server,))
        fjob.start()
        self._server.run_forever()


if __name__ == '__main__':
    device = '/dev/ttyUSB0'
    wsb = WSB(device)
    wsb.start()
