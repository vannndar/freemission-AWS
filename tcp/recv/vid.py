import cv2
import socket
import struct
import numpy as np
import time

TCP_IP = '52.221.232.251'  # Replace with your EC2's public IP
TCP_PORT = 9000

# Initialize camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise Exception("Could not open video device")

# Connect to server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        data = buffer.tobytes()
        frame_length = struct.pack('!I', len(data))  # 4-byte header (big-endian)
        # cv2.imshow('Echoed Video', frame)

        # Send frame to server
        s.sendall(frame_length)
        s.sendall(data)

        send = time.time()

        # Receive echoed frame
        header = s.recv(4)
        if not header:
            break
        echoed_length = struct.unpack('!I', header)[0]
        echoed_data = bytearray()
        while len(echoed_data) < echoed_length:
            chunk = s.recv(echoed_length - len(echoed_data))
            if not chunk:
                break
            echoed_data.extend(chunk)
        
        receive = time.time()
        print(f"Round-trip time: {receive - send:.2f}s")

        # Decode and display echoed frame
        echoed_frame = cv2.imdecode(np.frombuffer(echoed_data, dtype=np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow('Echoed Video', echoed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    s.close()