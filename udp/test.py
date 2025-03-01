import cv2
import socket
import numpy as np
import threading

UDP_IP = '54.255.24.228'  # ← REPLACE THIS
UDP_PORT = 9000

# Camera setup
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def receiver_thread():
    while True:
        try:
            data, _ = sock.recvfrom(65507)
            print(f"Received {len(data)} bytes")  # Add this line
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except:
            break

threading.Thread(target=receiver_thread, daemon=True).start()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        print(f"Sending {len(buffer)} bytes")  # Add this line
        sock.sendto(buffer.tobytes(), (UDP_IP, UDP_PORT))
finally:
    cap.release()
    sock.close()
    cv2.destroyAllWindows()