    import socket
import time

UDP_IP = '0.0.0.0'
UDP_PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("UDP server running...")
while True:
    try:
        data, addr = sock.recvfrom(65507)
        print(f"Received {len(data)} bytes from {addr}")
        sock.sendto(data, addr)
        print(f"Echoed back to {addr}")
    except Exception as e:
        print(f"Error: {e}")