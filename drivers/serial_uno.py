import serial, time, struct

class SerialUNO:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=1):
        self.port = port
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)
            print(f"[SerialUNO] Connected: {port} @ {baudrate}")
        except Exception as e:
            print(f"[SerialUNO] Failed to open {port}: {e}")
            self.ser = None

    def send(self, text: str):
        if self.ser:
            self.ser.write((text + '\n').encode())

    def send_speed_steer(self, v_mps: float, steer_deg: float):
        # Simple text protocol: V,<mps>,S,<deg>
        if self.ser:
            msg = f"V,{v_mps:.3f},S,{steer_deg:.1f}\n"
            self.ser.write(msg.encode())

    def read_line(self):
        if self.ser and self.ser.in_waiting:
            return self.ser.readline().decode(errors='ignore').strip()
        return None

    def close(self):
        try:
            if self.ser: self.ser.close()
        except Exception:
            pass
