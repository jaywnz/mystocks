#Author: Sunil Lal
#Modified by JW
#17 March 2021

#This is a simple HTTP server which listens on port 8080, accepts connection request, and processes the client request 
#in sepearte threads. It implements basic service functions (methods) which generate HTTP response to service the HTTP requests. 
#Currently there are 3 service functions; default, welcome and getFile. The process function maps the requet URL pattern to the service function.
#When the requested resource in the URL is empty, the default function is called which currently invokes the welcome function.
#The welcome service function responds with a simple HTTP response: "Welcome to my homepage".
#The getFile service function fetches the requested html or img file and generates an HTTP response containing the file contents and appropriate headers.

#To extend this server's functionality, define your service function(s), and map it to suitable URL pattern in the process function.

#This web server runs on python v3
#Usage: execute this program, open your browser (preferably chrome) and type http://servername:8080
#e.g. if server.py and broswer are running on the same machine, then use http://localhost:8080



from socket import *
import _thread
import pycurl
from lxml import etree
from io import BytesIO


serverSocket = socket(AF_INET, SOCK_STREAM)

serverPort = 8080
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(("", serverPort))

serverSocket.listen(5)
print('The server is running')	
# Server should be up and running and listening to the incoming connections

#Extract the given header value from the HTTP request message
def getHeader(message, header):

	if message.find(header) > -1:
		value = message.split(header)[1].split()[0]
	else:
		value = None

	return value

#service function to fetch the requested file, and send the contents back to the client in a HTTP response.
def getFile(filename):

	try:

		f = open(filename, "rb")
		# Store the entire content of the requested file in a temporary buffer
		body = f.read()

		# if the filename ends with (png||jpg) then set the Content-Type to be "image/(png||jpg)"
		if filename.endswith(('png', 'jpg')):
			contentType = "image/" + filename.split('.')[-1]
		# else set the Content-Type to be "text/html"
		else:
			contentType = "text/html"

		header = ("HTTP/1.1 200 OK\r\nContent-Type:" + contentType + "\r\n\r\n").encode()

	except IOError:

		# Send HTTP response message for resource not found
		header = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
		body = "<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n".encode()

	return header, body

#service function to generate HTTP response with a simple welcome message
def welcome(message):


	header = "HTTP/1.1 200 OK\r\n\r\n".encode()
	body = ("<html><head></head><body><h1>Welcome to my homepage</h1></body></html>\r\n").encode()


	return header, body



##location service function uses google API to return XML data about the requested location
def location(message):

	# So this is a web server which has just received an HTTP request from client. 
	#In order to service this request we need to connect to Google Map API server and pass on the request for location data
	#To do this we need another socket. Since we are requesting for data from Google server, we will be the client.
	#Google server requires secure HTTP connection (TLS/SSL) so we could create a client socket with ssl wrapper.
	#However pycurl provides a convenient way of communcating with an HTTPS server.

	#get the location name (e.g. auckland) from the client's HTTP GET request (e.g. /loc=auckland)
	resource = message.split()[1][1:].strip('loc=')

	#This is buffer to hold response from google map API server
	response_buffer = BytesIO()

	curl = pycurl.Curl()

	#Set the curl options which specify the Google API server, the parameters to be passed to the API,
	# and buffer to hold the response
	curl.setopt(curl.SSL_VERIFYPEER, False)
	curl.setopt(curl.URL, 'https://maps.googleapis.com/maps/api/geocode/xml?key=AIzaSyASAX7LnyXwY1pxZPYgIZY-baZqb1pIGnY&address="' + resource + '"')
	

	curl.setopt(curl.WRITEFUNCTION, response_buffer.write)

	curl.perform()
	curl.close()

	#create HTTP response just by simply relaying back Google server's response
	file = response_buffer.getvalue()

	#JW - parse the XML file and build response
	root = etree.fromstring(file)
	city = root.findtext("result[1]/address_component[1]/short_name")
	lat = root.findtext("result[1]/geometry/location/lat")
	lng = root.findtext("result[1]/geometry/location/lng")
	body = "<html><head></head><body><p>" + city + " is located at Latitude " + lat + " and Longitude " + lng + "</p></body></html>"

	body = body.encode()
	header = "HTTP/1.1 200 OK\r\n\r\n".encode()


	return header, body


#default service function
def default(message):

	header, body = welcome(message)

	return header, body


#We process client request here. The requested resource in the URL is mapped to a service function which generates the HTTP reponse 
#that is eventually returned to the client. 
def process(connectionSocket) :	
	# Receives the request message from the client
	message = connectionSocket.recv(1024).decode()


	if len(message) > 1:


		# Extract the path of the requested object from the message
		# Because the extracted path of the HTTP request includes
		# a character '/', we read the path from the second character
		resource = message.split()[1][1:]


		#map requested resource (contained in the URL) to specific function which generates HTTP response 
		if resource == "":
			responseHeader, responseBody = default(message)
		elif resource == "welcome":
			responseHeader,responseBody = welcome(message)
		elif "loc=" in resource:
			responseHeader,responseBody = location(message)
		else:
			responseHeader,responseBody = getFile(resource)


	# Send the HTTP response header line to the connection socket
	connectionSocket.send(responseHeader)
	# Send the content of the HTTP body (e.g. requested file) to the connection socket
	connectionSocket.send(responseBody)
	# Close the client connection socket
	connectionSocket.close()


#Main web server loop. It simply accepts TCP connections, and get the request processed in seperate threads.
while True:
	
	# Set up a new connection from the client
	connectionSocket, addr = serverSocket.accept()
	#Clients timeout after 60 seconds of inactivity and must reconnect.
	connectionSocket.settimeout(60)
	# start new thread to handle incoming request
	_thread.start_new_thread(process,(connectionSocket,))





