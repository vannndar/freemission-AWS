import cv2
import socket
import numpy as np
import time
import threading

UDP_IP = '52.221.232.251'  # Replace with your EC2 IP
UDP_PORT = 9000
MAX_FRAME_SIZE = 60000  # Max safe UDP payload size

# Camera settings (reduce resolution for better performance)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 25)

# UDP socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
last_frame_time = time.time()
current_frame = None
frame_lock = threading.Lock()

def receiver_thread():
    """Thread to receive and display frames"""
    global current_frame
    while True:
        try:
            data, _ = sock.recvfrom(MAX_FRAME_SIZE + 10)  # +10 for header
            timestamp = time.time()
            
            # Decode frame with timestamp check
            header = data[:10]
            frame_time = float(header.decode().strip())
            if timestamp - frame_time > 0.1:  # Drop frames older than 100ms
                continue
                
            frame = cv2.imdecode(np.frombuffer(data[10:], np.uint8), cv2.IMREAD_COLOR)
            with frame_lock:
                current_frame = frame
        except:
            break

# Start receiver thread
threading.Thread(target=receiver_thread, daemon=True).start()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Compress frame (adjust quality as needed)
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        
        # Add timestamp header (10-byte string)
        header = f"{time.time():10.5f}".encode()
        packet = header + buffer.tobytes()
        
        # Split into chunks if needed (rarely necessary with 640x360)
        if len(packet) > MAX_FRAME_SIZE:
            continue  # Skip frame if too big
            
        sock.sendto(packet, (UDP_IP, UDP_PORT))
        
        # Display latest received frame
        with frame_lock:
            if current_frame is not None:
                cv2.imshow('Video Stream', current_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cap.release()
    sock.close()
    cv2.destroyAllWindows()