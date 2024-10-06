import socket
import keyboard
import time

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 65432))
    sock.listen(1)

    conn, addr = sock.accept()
    print(f"Connected to {addr}")

    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            key = data.decode()
            if len(key) == 1 and key.isalnum():
                keyboard.send(key)
            time.sleep(0.01)

if __name__ == "__main__":
    main()
