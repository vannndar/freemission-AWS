import socket


TCP_IP = '54.255.24.228'
TCP_PORT = 9000
BUFFER_SIZE = 20
MESSAGE = "Hello, World!"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
try:
    while True:
        MESSAGE = input("Enter message to send (or type 'exit' to quit): ")
        if MESSAGE.lower() == 'exit':
            break
        
        s.send(MESSAGE.encode())
except Exception as e:
    print("Error:", e)
finally:
    s.close()
    print("Connection closed.")
