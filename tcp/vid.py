import socket
import struct

TCP_IP = '0.0.0.0'  # Listen on all interfaces
TCP_PORT = 9000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
print("Server is running...")

conn, addr = s.accept()
print(f"Connected by: {addr}")

try:
    while True:
        # Read the 4-byte header (frame length)
        header = conn.recv(4)
        if not header:
            break
        frame_length = struct.unpack('!I', header)[0]  # Decode big-endian unsigned int

        # Read the full frame data
        data = bytearray()
        while len(data) < frame_length:
            packet = conn.recv(frame_length - len(data))
            if not packet:
                break
            data.extend(packet)

        # Echo back the same header and data
        conn.sendall(header)
        conn.sendall(data)
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
    s.close()
