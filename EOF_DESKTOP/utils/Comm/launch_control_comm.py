"""
이 파일은 하드웨어 제어를 위한 통신 모듈입니다.
"""
import socket

from utils.debugging import current_date


class LaunchControlComm():
    """여러 라인의 프로그램 시작을 제어하기 위한 통신 클래스입니다."""
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"{current_date()} | Initialize LaunchControlComm")


    def __del__(self):
        self.client_socket.close()
        # print("LaunchControlComm소켓 반환 되었는가?")

    def activate(self) -> bool:
        """
        하드웨어를 제어할 명령을 보냅니다.

        Returns:
            bool: 성공할 경우 True를 반환
        """
        message = "/activate LANE_1"

        print(f"{current_date()} | Connect to {self.ip_address}:{self.port}...")
        self.client_socket.connect((self.ip_address, self.port))
        print(f"{current_date()} | Send activate message to {self.ip_address}:{self.port}.")
        self.client_socket.sendall(message.encode('utf-8'))
        self.client_socket.close()
        print(f"{current_date()} | Activate lane done.")

        return True
