"""
오디오 통신을 위한 모듈입니다.
"""
import socket


class AudioCommunication:
    """오디오 파일을 통신하기 위한 클래스입니다."""
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port

    def __del__(self):
        # self.client_socket.close()
        pass

    def send_msg(self, message):
        """오디오 파일을 송신합니다."""
        server_address = (self.ip_address, self.port)
        print(f"Connecting to {server_address}...")

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.ip_address, self.port))
        client_socket.sendall(message.encode('utf-8'))
        client_socket.close()

        print("File sent successfully.")
