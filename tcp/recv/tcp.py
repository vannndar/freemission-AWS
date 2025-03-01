import socket


TCP_IP = '54.255.24.228'
TCP_PORT = 9000
BUFFER_SIZE = 20
MESSAGE = "Hello, World!"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE.encode())
data = s.recv(BUFFER_SIZE)
s.close()

print ("received data:", data)