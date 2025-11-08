# Camera free-space detector (RoboCam)
import cv2, numpy as np, time, atexit

class Perceiver:
    def __init__(self, cfg):
        self.cfg = cfg
        self.SHOW_DEBUG = False
        self.FW = cfg.get('camera', {}).get('frame_w', 320)
        self.FH = cfg.get('camera', {}).get('frame_h', 240)
        self.ROI_Y_RATIO = cfg.get('camera', {}).get('roi_y_ratio', 0.66)
        self._rcam = None
        try:
            from RoboCam.robocam import RoboCam
            self.RoboCam = RoboCam
            print("[Perceiver] RoboCam available")
        except Exception as e:
            self.RoboCam = None
            print("[Perceiver] RoboCam not available:", e)

    def _ensure_started(self):
        if self._rcam is None and self.RoboCam is not None:
            cam = self.RoboCam()
            cam.CameraStreamInit(width=self.FW, height=self.FH)
            time.sleep(1.0)
            cam.CameraStream()
            time.sleep(1.0)
            self._rcam = cam
        return self._rcam

    def get_frame(self):
        cam = self._ensure_started()
        if cam is None:
            return None
        frame = getattr(cam, "_RoboCam__raw_img", None)
        if frame is None:
            return None
        h, w = frame.shape[:2]
        if (w, h) != (self.FW, self.FH):
            frame = cv2.resize(frame, (self.FW, self.FH))
        return frame

    def freespace_center_offset(self, frame):
        if frame is None:
            return None, {}
        h, w = frame.shape[:2]
        y0 = int(h * self.ROI_Y_RATIO)
        roi = frame[y0:, :]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 0, 80], dtype=np.uint8)
        upper = np.array([179, 60, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower, upper)
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return None, {"roi": roi, "mask": mask}
        c = max(cnts, key=cv2.contourArea)
        M = cv2.moments(c)
        if M["m00"] == 0:
            return None, {"roi": roi, "mask": mask}
        cx = int(M["m10"]/M["m00"])
        offset = cx - (w // 2)
        return offset, {"roi": roi, "mask": mask}

    def shutdown(self):
        try:
            if self._rcam is not None:
                self._rcam.CameraStreamOff()
        except Exception:
            pass
        self._rcam = None
atexit.register(lambda: None)
