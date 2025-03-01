import socket

TCP_IP = '54.255.24.228'
TCP_PORT = 9999
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

try:
    while True:
        data = s.recv(BUFFER_SIZE)
        if not data:
            break
        print("Received data:", data.decode())  # Pastikan data didecode sebelum dicetak
except Exception as e:
    print("Error:", e)
finally:
    s.close()
    print("Connection closed.")


# # Add timestamp at the end of the file
# send_time = str(time.time()).encode()  # Convert float timestamp to bytes
# file_data += b"###TIMESTAMP###" + send_time  # Append timestamp

# received_time = time.time()
# if b"###TIMESTAMP###" in data:
#     sent_time = float(data.split(b"###TIMESTAMP###")[-1])
#     rtt = received_time - sent_time
#     print(f"Round-trip time: {rtt:.6f} seconds")
# else:
#     print("Timestamp missing. Check if B and C forwarded data correctly.")
