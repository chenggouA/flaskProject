
import cv2
class camera:

    def __init__(self, transforms, index = 0):
        self.index = index
        self.transforms = transforms
        self.cap = cv2.VideoCapture(self.index)
    
    def get_frame(self):
        while True:
            flag, frame = self.cap.read()
            if not flag:
                return 
            for transform in self.transforms:
                frame = transform.inference(frame) 

            _, frame = cv2.imencode(".jpg", frame)
            yield frame.tobytes()
