from queue import Queue
import numpy as np
import cv2
from typing import List

class frame:
    def __init__(self, has_frame = False):
        self.has_frame = has_frame
        self.frame = None

    def get_frame(self)-> np.ndarray:

        return self.frame
    
class CameraStream:

    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        assert self.cap.isOpened(), "加载失败"
        self.clients: List[frame] = []

    def subscribe(self)-> frame:
        f = frame()
        self.clients.append(f)
        return f
    
    def unsubscribe(self, frame):
        self.clients.remove(frame)

    def get_frame(self, frame):
        if frame.has_frame:
            new_frame = frame.get_frame()
            
        else:
            _, new_frame = self.cap.read()
            for client in self.clients:
                client.frame = new_frame
                client.has_frame = True
        
        frame.has_frame = False
        _, f = cv2.imencode(".jpg", new_frame)
        return (b'--frame\n'
               b'Content-Type: image/jpeg\r\n\r\n' + f.tobytes() + b'\r\n')