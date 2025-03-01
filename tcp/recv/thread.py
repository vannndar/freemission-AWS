import cv2
import socket
import struct
import numpy as np
import threading
from collections import deque
import time

TCP_IP = '52.221.232.251'  # Replace with your EC2 IP
TCP_PORT = 9000
MAX_QUEUE_SIZE = 60  # Limit frame buffer to prevent lag

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 10)

# Thread-safe frame queue
send_queue = deque(maxlen=MAX_QUEUE_SIZE)
stop_event = threading.Event()

# Network connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

def sender_thread():
    """Thread to send frames from queue"""
    while not stop_event.is_set():
        if send_queue:
            frame_data = send_queue.popleft()
            try:
                # Send frame length header + frame data
                s.sendall(struct.pack('!I', len(frame_data)))  # 4-byte header
                s.sendall(frame_data)
            except (BrokenPipeError, ConnectionResetError):
                stop_event.set()
                break

def receiver_thread():
    """Thread to receive echoed frames"""
    while not stop_event.is_set():
        try:
            # Read header first
            header = s.recv(4)
            if not header:
                break
            
            # Get frame length from header
            frame_length = struct.unpack('!I', header)[0]
            
            # Read frame data
            data = bytearray()
            while len(data) < frame_length:
                packet = s.recv(frame_length - len(data))
                if not packet:
                    break
                data.extend(packet)
            
            # Decode and display frame
            frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
            frame = cv2.putText(frame, time.ctime(), (10, 70 ), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.imshow('Echoed Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break
        except (ConnectionAbortedError, ConnectionResetError):
            stop_event.set()
            break

# Start threads
sender = threading.Thread(target=sender_thread)
receiver = threading.Thread(target=receiver_thread)
sender.daemon = True
receiver.daemon = True
sender.start()
receiver.start()

try:
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.putText(frame, time.ctime(), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
        # Compress frame and add to queue
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        send_queue.append(buffer.tobytes())
finally:
    stop_event.set()
    cap.release()
    s.close()
    cv2.destroyAllWindows()
    sender.join()
    receiver.join()