import time

class SafetySystem:
    def __init__(self, controller, timeout_s=5.0):
        self.controller = controller
        self.last_hb = time.time()
        self.timeout_s = timeout_s

    def check_heartbeat(self):
        if time.time() - self.last_hb > self.timeout_s:
            print("[Safety] Watchdog timeout – STOP")
            self.controller.stop_all()
            self.last_hb = time.time()

    def heartbeat(self):
        self.last_hb = time.time()
