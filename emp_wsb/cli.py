from emp_wsb.wsb import WSB
import fire


def run(device=None, port=9000):
    if not device:
        raise SystemExit('args[device] cannot be None!')
    wsb = WSB(device, port=port)
    wsb.start()


def entry_points():
    fire.Fire({
        'run': run
    })
