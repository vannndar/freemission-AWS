import socket
import struct
import threading

TCP_IP = '0.0.0.0'
TCP_PORT = 9000

def handle_client(conn):
    """Handle individual client connection"""
    try:
        while True:
            # Read frame length header
            header = conn.recv(4)
            if not header:
                break
            
            frame_length = struct.unpack('!I', header)[0]
            
            # Read frame data
            data = bytearray()
            while len(data) < frame_length:
                packet = conn.recv(frame_length - len(data))
                if not packet:
                    break
                data.extend(packet)
            
            # Echo back immediately
            conn.sendall(header)
            conn.sendall(data)
    finally:
        conn.close()

# Main server setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(5)  # Allow multiple connections
print("Server is running...")

while True:
    conn, addr = s.accept()
    print(f"Connected: {addr}")
    client_thread = threading.Thread(target=handle_client, args=(conn,))
    client_thread.daemon = True
    client_thread.start()
