import socket

TCP_IP = '0.0.0.0'
TCP_PORT = 9000  # Port for receiving from A
BUFFER_SIZE = 1024  # Increased buffer size

TCP_SEND_PORT = 9999  # Port for sending to C

# Socket to receive data from A
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

print("Waiting for connections...")
conn, addr = s.accept()
print('Connected to A:', addr)

# Socket to send data to C
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.bind((TCP_IP, TCP_SEND_PORT))
c.listen(1)

connSend, addrSend = c.accept()
print('Connected to C:', addrSend)

while True:
    data = conn.recv(BUFFER_SIZE)
    if not data:
        break
    print("Received from A:", data.decode())

    connSend.send(data)  # Forward data to C
    print("Forwarded to C.")

conn.close()
connSend.close()
print("Connections closed.")
