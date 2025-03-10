import socket


TCP_IP = '0.0.0.0'
TCP_PORT = 9000
BUFFER_SIZE = 20  # Normally 1024, but we want fast response

TCP_SEND_PORT = 9999

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.bind((TCP_IP, TCP_SEND_PORT))
c.listen(1)


conn, addr = s.accept()
connSend, addrSend = c.accept()
print ('Connection address:', addr)
while 1:
    data = conn.recv(BUFFER_SIZE)
    if not data: break
    print ("received data:", data)
    conn.send(data)  # echo
conn.close() 
