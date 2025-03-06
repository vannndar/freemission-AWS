import socket
import cv2
import numpy as np
import struct

# Set up IP and ports
EC2_IP = "<EC2_PUBLIC_IP>"  # Replace with your EC2's public IP address
UDP_PORT_RECEIVE = 8081  # Port to receive video data from EC2
UDP_PORT_SEND = 8080  # Port to send video to EC2

# Create UDP socket for sending data to EC2
sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ec2_address = (EC2_IP, UDP_PORT_RECEIVE)

# Create UDP socket for receiving video from EC2
sock_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_receive.bind(("0.0.0.0", UDP_PORT_SEND))

# Send a "hello" message to the EC2 server to let it know the laptop's IP
sock_send.sendto(b"Laptop ready", ec2_address)
print("Laptop's IP sent to EC2.")

# Now receive video data from EC2 and display it
while True:
    try:
        # Receive video data from EC2
        data, addr = sock_receive.recvfrom(65535)  # Max UDP packet size
        print(f"Received {len(data)} bytes from EC2")

        # Decode and display the frame
        frame_length = struct.unpack("!I", data[:4])[0]
        frame_data = data[4 : 4 + frame_length]
        frame = cv2.imdecode(
            np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR
        )

        if frame is not None:
            cv2.imshow("Video Stream", frame)
        else:
            print("Failed to decode video frame")

    except Exception as e:
        print(f"Error: {e}")

    # Press 'q' to close the video window
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
sock_receive.close()
sock_send.close()
