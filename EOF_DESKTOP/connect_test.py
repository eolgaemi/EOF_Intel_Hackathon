import socket


host = '0.0.0.0'
port = 28999

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))

    print(f"포트로 {port}로 수신중...")
    server_socket.listen(1)

    client_socket, addr = server_socket.accept()
    print(f"{addr}에서 연결됨.")

    while True:
        message = client_socket.recv(1024).decode()
        if not message:
            break
        print(f"Client: {message}")

        reply = input("Input message >> ")
        client_socket.send(reply.encode())
    
    client_socket.close()
    server_socket.close()