from emp_wsb.wsb import WSB
import sys


def cli():
    device = sys.argv[1]
    wsb = WSB(device)
    wsb.start()


if __name__ == '__main__':
    cli()
