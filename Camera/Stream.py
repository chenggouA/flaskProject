from queue import Queue
import numpy as np
from datetime import datetime
from typing import List

class frames:
    def __init__(self):
        self.q = Queue()
        self.last_time = datetime.now()

    def get_frame(self):
        self.last_time = datetime.now() # 更新时间
        return self.q.get()
    
    def put(self, frame):
        self.q.put(frame)
class CameraStream:

    def __init__(self):
        self.clients: List[frames] = []

    def subscribe(self):
        frame = frames()
        self.clients.append(frame)
        print("有新用户进行连接")
        return frame
    
    def unsubscribe(self, frame):
        self.clients.remove(frame)

    def _getTimeDiff(self, last_time)-> "int > 0":
        current_time = datetime.now()
        diff = current_time - last_time 
        return int(diff.total_seconds())

    def update_frame(self, frame):
        
        # 检查存活状体
        orign_count = len(self.clients)
        self.clients = [client for client in self.clients if self._getTimeDiff(client.last_time) < 2]
        if len(self.clients) < orign_count:
            print("用户退出连接")
        for frames in self.clients:
            frames.put(frame)
