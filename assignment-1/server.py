# 159.352 Assignment 1
# Author: JW based on server3.py by Sunil Lal

from socket import *
from base64 import b64encode
from io import BytesIO
import _thread
import pycurl
import json
from pathlib import Path

serverSocket = socket(AF_INET, SOCK_STREAM)

serverPort = 8080
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(("", serverPort))

serverSocket.listen(5)
print('The server is running.')

# Extract the given header value from the HTTP request message
def getHeader(message, header):

    if message.find(header) > -1:
        # Extract authorisation key
        value = message.split(header)[1].split()[2]
    else:
        value = None
    return value

# Fetch the requested file and send the contents back to the client in a HTTP response
def getFile(filename):

    try:
        path = Path(__file__).with_name(filename)
        with path.open("rb") as file:
            body = file.read()

        # Set correct Content-Type for images
        if filename.endswith(('png', 'jpg')):
            contentType = "image/" + filename.split('.')[-1]
        elif filename.endswith(('json')):
            contentType = "application/json"
        elif filename.endswith(('css')):
            contentType = "text/css"
        elif filename.endswith(('js')):
            contentType = "text/javascript"    
        else:
            contentType = "text/html"

        header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()

    except IOError:

        # Send HTTP response message for resource not found
        header = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
        body = "<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n".encode()

    return header, body


# Serve a simple homepage
def home():

    header = "HTTP/1.1 200 OK\r\n\r\n".encode()
    body = "<html><head></head><body><h1>Welcome to my homepage</h1></body></html>\r\n".encode()

    return header, body


# Process the client's request
def process(connectionSocket) :	
    # Receives the request message from the client
    message = connectionSocket.recv(1024).decode()

    if len(message) > 1:

        # Extract the path of the requested object from the message
        resource = message.split()[1][1:]

        if auth == False:
            responseHeader, responseBody = authenticate(message)
        else:
            if resource == "portfolio":
                responseHeader, responseBody = showPortfolio()
            elif resource == "stock":
                responseHeader, responseBody = showStock()
            elif resource == "":
                responseHeader, responseBody = home()
            else:
                responseHeader, responseBody = getFile(resource)

    # Send the HTTP response header line to the connection socket
    connectionSocket.send(responseHeader)
    # Send the content of the HTTP body (e.g. requested file) to the connection socket
    connectionSocket.send(responseBody)
    # Close the client connection socket
    connectionSocket.close()


#Function to split message and return HTTP protocol
def getProtocol(message) :

    x = message.split(" ")
    protocol = x[0]
    
    return protocol


#Carries out basic HTTP authentication
def authenticate(message) :

    # Assuming only one user
    serverCreds = b64encode(b"20020003:20020003").decode()

    if getHeader(message, "Authorization") == None:
        print("Authorising client.")
        header = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Please enter your credentials.\", charset=\"UTF-8\"\r\n\r\n".encode()
        body = "<html><head></head><body><h1>Login</h1><p>Please enter your credentials to access this site.</p></body></html>\r\n".encode()
        return header, body
    elif getHeader(message, "Authorization") == serverCreds:
        print("User logged in.")
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head></head><body><h1>Success!</h1><p>User logged in.</p></body></html>\r\n".encode()
        global auth
        auth = True
        return header, body
    else:
        print("Invalid credentials.")
        header = "HTTP/1.1 403 Forbidden\r\n\r\n".encode()
        body = "<html><head></head><body><h1>Invalid login</h1><p>Please enter the correct credentials to access this site.</p></body></html>\r\n".encode()
        return header, body


# Parse portfolio information from a JSON file and serve it
def showPortfolio() :
    print("Showing portfolio...")

    path = Path(__file__).with_name('portfolio.html')
    with path.open("rb") as file:
        body = file.read()

    # Retrieve list of stock symbols
    response_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, False)
    curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/ref-data/symbols?token=pk_dc1d04cb0f2c4bc5b81af61256b2fd47')
    curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
    curl.perform()
    curl.close()

    # Load all symbols into JSON file from memory buffer
    allSymbols = json.loads(response_buffer.getvalue().decode('UTF-8'))

    # Filter only those symbols of type 'cs'
    csSymbols = [x for x in allSymbols if x['type'] == 'cs']

    # Save filtered symbols to same directory as Python script
    path = Path(__file__).with_name('cs.json')
    with path.open("w") as file:
        json.dump(csSymbols, file)

    header = "HTTP/1.1 200 OK\r\n\r\n".encode()

    return header, body

    # Use list to populate select on portfolio.html

    # Store the ticker symbol
    # Store the quantity purchased
    # Store the purchase price
    # Validate user changes
    # Update the portfolio.json file with HTTP POST request


    # header = "HTTP/1.1 200 OK\r\n\r\n".encode()
    # body = "<html><head></head><body><h1>Portfolio</h1><p>This is your portfolio site.</p></body></html>\r\n".encode()

    # return header, body

# Plot stock graph
def showStock() :
    print("Showing stock...")

    # TODO

    header = "HTTP/1.1 200 OK\r\n\r\n".encode()
    body = "<html><head></head><body><h1>Stock</h1><p>This is your stock site.</p></body></html>\r\n".encode()

    return header, body


# Set initial user authentication
auth = False

# Main web server loop
while True:
    
    # Set up a new connection from the client
    connectionSocket, addr = serverSocket.accept()
    # Clients timeout after 60 seconds of inactivity and must reconnect
    connectionSocket.settimeout(60)
    # Start new thread to handle incoming request
    _thread.start_new_thread(process,(connectionSocket,))





