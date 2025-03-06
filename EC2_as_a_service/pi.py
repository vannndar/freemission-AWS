import cv2
import socket
import time
import numpy as np

# Set up the UDP socket to send data to the EC2 server
UDP_IP = "<EC2_PUBLIC_IP>"  # Replace with your EC2 public IP
UDP_PORT = 8080  # The port EC2 will listen on for video data

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Initialize the camera (Raspberry Pi's default camera)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Capturing video and sending it to EC2...")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to capture image.")
        break

    # Convert the frame to JPEG
    _, encoded_frame = cv2.imencode(".jpg", frame)

    # Send the frame to EC2 over UDP
    sock.sendto(encoded_frame.tobytes(), (UDP_IP, UDP_PORT))

    # Optional: Add a delay to simulate real-time video streaming
    time.sleep(0.03)

cap.release()
sock.close()
