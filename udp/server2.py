    import socket
import time

UDP_IP = '0.0.0.0'
UDP_PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

UDP_RECV_PORT = 9999

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind((UDP_IP, UDP_RECV_PORT))

print("UDP server running...")
while True:
    try:
        data, addr = sock.recvfrom(65507)
        print(f"Received {len(data)} bytes from {addr}")
        sock2.sendto(data, addr)
        print(f"Echoed back to {addr}")
    except Exception as e:
        print(f"Error: {e}")