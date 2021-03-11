# Author: Sunil Lal
# Modified by JW
# 11 March 2021

#This is a very basic HTTP server which listens on port 8080, 
#and serves the same response messages regardless of the browser's request. It runs on python v3
#Usage: execute this program, open your browser (preferably chrome) and type http://servername:8080
#e.g. if server.py and broswer are running on the same machine, then use http://localhost:8080

# Import the required libraries
from socket import *

# Listening port for the server
serverPort = 8080

# Create the server socket object
serverSocket = socket(AF_INET,SOCK_STREAM)

# Bind the server socket to the port
serverSocket.bind(('',serverPort))

# Start listening for new connections
serverSocket.listen(1)

print('The server is ready to receive messages.')

while 1:
    # Accept a connection from a client
	connectionSocket, addr = serverSocket.accept()

	# Retrieve the message sent by the client
	request = connectionSocket.recv(1024)

	# Parse request into list
	splitRequest = (request.decode()).split(' ')
	pathRequest = splitRequest[1]
	print("Client requested " + pathRequest)

	if(pathRequest == '/'):
		file = 'index.html'
	else:
		file = pathRequest.lstrip('/')

	try:
		f = open(file, 'rb')
		body = f.read()
		f.close()
		header = 'HTTP/1.1 200 OK\n\n'
	except:
		body = '<html><body><p>The requested file was not found on the server.</p></body></html>'
		body = body.encode()
		header = 'HTTP/1.1 404 Not Found\n\n'
	
	header = header.encode()
	response = header + body

	# Send HTTP response back to the client
	connectionSocket.send(response)

    # Close the connection
	connectionSocket.close()