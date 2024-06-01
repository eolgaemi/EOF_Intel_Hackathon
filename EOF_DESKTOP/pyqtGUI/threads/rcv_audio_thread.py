"""
오디오 통신을 위한 스레드 모듈입니다.
"""
import time
import socket

from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from utils.debugging import current_date
from utils.Audio.voice_record import AudioRecorder


class ReceiveAudio(QThread):
    """오디오 통신을 위한 스레드 객체 입니다."""
    rcv_audio_signal = pyqtSignal()

    def __init__(self, ip_address, port):
        super().__init__()
        self.ip_address = ip_address
        self.port = port

        self.recorder = AudioRecorder()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind((self.ip_address, self.port))
        self.socket.listen(1)
        self.running = True
        print(f"{current_date()} | Initialize ReceiveAudio")

    def __del__(self):
        self.socket.close()

    def run(self):
        """클라이언트에서 녹음요청 명령을 수신합니다."""
        while self.running:
            print("녹음요청을 기다리고 있습니다...")
            server_socket, _ = self.socket.accept()
            print(f"서버와 연결됨: {server_socket}")
            self.msg = server_socket.recv(1024).decode('utf-8')
            print("서버로부터 받은 메시지: ", self.msg)
            time.sleep(0.1)

            if self.msg == "Do Record":
                self.recorder.record_and_save()
                self.rcv_audio_signal.emit()

    def stop(self):
        """스레드를 종료합니다."""
        self.running = False
        time.sleep(1)
