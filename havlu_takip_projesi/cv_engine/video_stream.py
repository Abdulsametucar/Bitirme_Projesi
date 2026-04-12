import cv2

class VideoStream:
    def __init__(self, source=0):
        self.source = source
        self.capture = cv2.VideoCapture(source)

    def read(self):
        if not self.capture.isOpened():
            return None
        ret, frame = self.capture.read()
        if not ret:
            return None
        return frame

    def reset(self):
        if self.capture.isOpened():
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def release(self):
        if self.capture.isOpened():
            self.capture.release()
