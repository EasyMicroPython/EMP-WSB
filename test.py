from wsServer import WebsocketServer
from emptool import Pyboard, PyboardError
from emptool import get
import serial
import threading
import os

repl = serial.Serial('/dev/ttyUSB0', 115200)
get_file = False


def new_client(client, server):
    print("New client connected and was given id %d" % client['id'])
    # server.send_message_to_all("Hey all, a new client has joined us")
    # get(Pyboard(repl), 'boot.py')


# Called for every client disconnecting


def client_left(client, server):
    print("Client(%d) disconnected" % client['id'])


# Called when a client sends a message
def message_received(client, server, message):
    print(message)
    repl.write(message.encode('utf-8'))


def binary_received(client, server, message):
    print("binary: ", message)
    repl.write(message)


def repl_output(server):
    frame = ''
    sendPDU = True
    while True:
        if WebsocketServer.clients:
            data = repl.read().decode()
            server.send_message(WebsocketServer.clients[0], data)

            # frame += data
            # if frame.count('[+emp pdu+]\n\n') == 1:
            #     sendPDU = False
                
            # if sendPDU:
            #     server.send_message(WebsocketServer.clients[0], data)

            # if frame.count('[+emp pdu+]\n\n') == 2:
            #     frame = frame.split('[+emp pdu+]')[1]
            #     server.send_message(WebsocketServer.clients[0], frame)
            #     frame = ''
            #     sendPDU = True


# def read_until():

PORT = 9000
server = WebsocketServer(PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
server.set_fn_binary_recevived(binary_received)

mthread = threading.Thread(target=repl_output, args=(server,))
mthread.start()
server.run_forever()
