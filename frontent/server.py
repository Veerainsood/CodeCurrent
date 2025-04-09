import socket

# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind to 127.0.0.1 (your own computer) on port 9999
server_socket.bind(('127.0.0.1', 9999))

# Wait for a connection
server_socket.listen(1)
print("Server is listening on 127.0.0.1:9999...")

# Accept a connection
conn, addr = server_socket.accept()
print(f"Connected by {addr}")

# Receive data from the client
data = conn.recv(1024)
print(f"Server received: {data.decode()}")

# Send a response
conn.sendall(b'Hello from server!')

# Close the connection
conn.close()
