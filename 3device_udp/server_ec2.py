import socket

# Set up IP and ports for EC2 server
UDP_IP = "0.0.0.0"  # EC2 listens on all interfaces
UDP_PORT_RECEIVE = 8080  # Port to receive video from Raspberry Pi
UDP_PORT_SEND = 8081  # Port to send video to Laptop

# Create UDP socket for receiving data from Raspberry Pi
sock_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_receive.bind((UDP_IP, UDP_PORT_RECEIVE))

# Create UDP socket for sending data to the laptop
sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Wait to receive a message from the laptop to get its IP address
print("Waiting for laptop to send its IP address...")
laptop_address = None
while laptop_address is None:
    try:
        # Listen for the laptop's message (it will contain the laptop's IP)
        data, addr = sock_receive.recvfrom(65535)  # Max UDP packet size
        if data == b"Laptop ready":  # A simple message to confirm laptop is ready
            laptop_address = addr  # Capture the laptop's IP and port
            print(f"Laptop connected: {laptop_address}")
    except Exception as e:
        print(f"Error: {e}")

while True:
    try:
        # Receive video data from Raspberry Pi
        data, addr = sock_receive.recvfrom(65535)  # Max UDP packet size
        print(f"Received {len(data)} bytes from {addr}")

        # Forward the data to the laptop
        sock_send.sendto(data, laptop_address)
        print("Data forwarded to laptop.")

    except Exception as e:
        print(f"Error: {e}")
