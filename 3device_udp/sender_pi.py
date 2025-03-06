import cv2
import socket
import struct
import numpy as np

# Set up IP and port for EC2 server
EC2_IP = "<EC2_PUBLIC_IP>"  # Replace with your EC2's public IP address
UDP_PORT_SEND = 8080  # Port to send video data to EC2

# Create UDP socket to send data to EC2
sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ec2_address = (EC2_IP, UDP_PORT_SEND)

# Initialize camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise Exception("Could not open video device")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Encode frame to JPEG
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    data = buffer.tobytes()

    # Create packet with frame length and data
    frame_length = struct.pack("!I", len(data))
    packet = frame_length + data

    # Send the packet to the EC2 server
    sock_send.sendto(packet, ec2_address)
    print(f"Sent {len(packet)} bytes to EC2 server.")

cap.release()
sock_send.close()
