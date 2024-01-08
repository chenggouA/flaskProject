from queue import Queue
import numpy as np
from typing import List
class CameraStream:

    def __init__(self, max_len = 200):
        self.max_len: int = max_len
        self.clients: List[Queue] = []
        self.last_frame = None

    def subscribe(self):
        queue = Queue()
        self.clients.append(queue)
        return queue
    
    def unsubscribe(self, queue):
        self.clients.remove(queue)

    def update_frame(self, frame):
        
        for client in self.clients:
            print(client.qsize())
            # if client.qsize() >= self.max_len:
            #     client.get()
            client.put(frame)