from wsb import WSB

if __name__ == '__main__':
    wsb = WSB('/dev/ttyUSB0')
    wsb.start()
