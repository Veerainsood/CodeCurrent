import socket

# Create a TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to 127.0.0.1 (yourself) on port 9999
client_socket.connect(('127.0.0.1', 9999))

# Send a message to the server
client_socket.sendall(b'Hello from client!')

# Receive the response
data = client_socket.recv(1024)
print(f"Client received: {data.decode()}")

# Close the connection
client_socket.close()
