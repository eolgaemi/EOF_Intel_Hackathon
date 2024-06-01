"""
이미지 스트림을 위한 스레드 모듈입니다.
"""
import time
import socket
import struct

import cv2
import numpy as np
from PyQt5.QtCore import QThread

from utils.debugging import current_date


class StreamImage(QThread):
    """이미지 스트림을 위한 스레드 객체입니다."""
    def __init__(self, frame_queue):
        super().__init__()
        self.camera = cv2.VideoCapture(0)
        self.frame_queue = frame_queue
        self.running = True
        print(f"{current_date()} | Initialize StreamImage")

    def __del__(self):
        self.camera.release()

    def run(self):
        while self.running:
            _, frame = self.camera.read()
            self.frame_queue.put(frame)

    def stop(self):
        """스레드를 종료합니다."""
        self.running = False
        time.sleep(1)
        # self.quit()
