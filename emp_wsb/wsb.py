import threading
import serial
from wsServer import WebsocketServer


class WSB:
    def __init__(self, device, baudrate=115200, port=9000):
        self._repl = serial.Serial(device, baudrate)
        self._server = WebsocketServer(port)
        self._server.set_fn_new_client(self._new_client)
        self._server.set_fn_client_left(self._client_left)
        self._server.set_fn_message_received(self._message_received)
        self._timer = None

    def _new_client(self, client, server):
        print("==> EMP-IDE Connected!")

    def _client_left(self, client, server):
        print("==> EMP-IDE Disconnected!")

    def _message_received(self, client, server, message):
        print("--> Message received: %s" % message)
        self._repl.write(message.encode('utf-8'))

    # 转发函数
    def _forward(self, server):
        def poll():
            if WebsocketServer.clients:
                data = self._repl.read().decode()
                try:
                    server.send_message(WebsocketServer.clients[0], data)
                except:
                    pass

            self._timer = threading.Timer(0.001, poll)
            self._timer.start()

        self._timer = threading.Timer(0.001, poll)
        self._timer.start()

    def start(self):
        _fthread = threading.Thread(target=self._forward, args=(self._server,))
        _fthread.start()
        self._server.run_forever()
