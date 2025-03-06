from flask import Flask, Response
import socket
import cv2
import numpy as np
import time  # Import time module to measure latency

app = Flask(__name__)

# Set up the UDP socket to receive video data from Raspberry Pi
UDP_IP = "0.0.0.0"  # EC2 listens on all interfaces
UDP_PORT = 8081  # Port to receive video data from the Pi

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))


# Function to continuously receive frames and stream them to the browser
def generate_frames():
    while True:
        start_time = time.time()  # Record the time at the start of frame processing

        # Receive video data from Raspberry Pi
        data, addr = sock.recvfrom(65536)  # Max UDP packet size
        np_arr = np.frombuffer(data, np.uint8)  # Convert the byte data to numpy array
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Decode the image

        if frame is None:
            print("Error: Failed to decode frame.")
            continue

        # Encode the frame as JPEG
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        # Calculate latency (time taken for frame processing)
        latency = time.time() - start_time  # Difference between start and end time

        # Print the latency to the console (can be logged as well)
        print(f"Frame latency: {latency:.4f} seconds")

        # Yield the frame in MJPEG format
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n\r\n"
        )


# Web route for video stream
@app.route("/video")
def video():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# Run the web server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # EC2 listens on port 5000
