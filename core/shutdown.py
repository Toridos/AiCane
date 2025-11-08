import signal, sys

def _handle(sig, frame):
    print(f"[Shutdown] Signal {sig} received")
    sys.exit(0)

def register_shutdown():
    signal.signal(signal.SIGINT, _handle)
    signal.signal(signal.SIGTERM, _handle)
