import cv2
import socket
import struct
import numpy as np
import time

UDP_IP = "54.179.14.35"  # Replace with your EC2's public IP
UDP_PORT = 9000

# Initialize camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise Exception("Could not open video device")

# Create UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (UDP_IP, UDP_PORT)

# Set timeout for receiving packets (adjust as needed)
s.settimeout(5)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Encode frame to JPEG
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        data = buffer.tobytes()

        # Create packet with header
        frame_length = struct.pack("!I", len(data))
        packet = frame_length + data

        # Send frame to server
        send_time = time.time()
        s.sendto(packet, server_address)

        try:
            # Receive echoed frame
            echoed_packet, addr = s.recvfrom(65535)  # Max UDP packet size
            rtt = time.time() - send_time
            print(f"Round-trip time: {rtt:.2f}s")

            # Validate and unpack response
            if len(echoed_packet) >= 4:
                echoed_length = struct.unpack("!I", echoed_packet[:4])[0]
                echoed_data = echoed_packet[4 : 4 + echoed_length]

                if len(echoed_data) == echoed_length:
                    echoed_frame = cv2.imdecode(
                        np.frombuffer(echoed_data, dtype=np.uint8), cv2.IMREAD_COLOR
                    )
                    if echoed_frame is not None:
                        cv2.imshow("Echoed Video", echoed_frame)
                    else:
                        print("Failed to decode echoed frame")
                else:
                    print("Data length mismatch")
            else:
                print("Invalid packet received")

        except socket.timeout:
            print("Timeout waiting for response")

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    s.close()
