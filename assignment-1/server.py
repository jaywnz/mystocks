# 159.352 Assignment 1
# Author: JW based on server3.py by Sunil Lal

from socket import *
from base64 import b64encode
from io import BytesIO
import _thread
import pycurl
import json
from pathlib import Path
import plotly.express as px
import re

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

    except OSError:
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
def process(connectionSocket):	
    # Receives the request message from the client
    message = connectionSocket.recv(1024).decode()

    method = getMethod(message)
    if method == "POST":
        responseHeader, responseBody = processForm(message)
    elif len(message) > 1:

        # Extract the path of the requested object from the message
        resource = message.split()[1][1:]

        query = re.search(r'server\.py\?symbol\=[A-Z]+', resource)
        
        if auth == False:
            responseHeader, responseBody = authenticate(message)
        else:
            if query is not None:
                responseHeader, responseBody = makePlot(resource)
            elif resource == "portfolio":
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


# Split message and return HTTP method
def getMethod(message):
    x = message.split(" ")
    method = x[0]
    
    return method


# Carry out basic HTTP authentication
def authenticate(message):
    # Assuming only one user
    serverCreds = b64encode(b"***REMOVED***:***REMOVED***").decode()

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


# Retrieve list of stock symbols from IEX Cloud as cs.json
def getSymbols():

    # Retrieve list of stock symbols
    response_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, False)
    curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/ref-data/symbols?token=***REMOVED***')
    curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
    curl.perform()
    curl.close()

    # Load all symbols into JSON object from memory buffer
    allSymbols = json.loads(response_buffer.getvalue().decode('UTF-8'))

    # Filter only those symbols of type 'cs'
    csSymbols = [x for x in allSymbols if x['type'] == 'cs']

    # Save filtered symbols to same directory as Python script
    path = Path(__file__).with_name('cs.json')
    with path.open("w") as file:
        json.dump(csSymbols, file)
    
    return

def calcGains():
    # Read portfolio, extract symbol and stored price
    path = Path(__file__).with_name('portfolio.json')
    with path.open("r") as file:
        portfolio = json.load(file)

    for record in portfolio:
        symbol = record["symbol"]
        price = record["price"]

        # API call to retrieve symbol details
        response_buffer = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(curl.SSL_VERIFYPEER, False)
        curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/stock/' + symbol + '/quote?token=***REMOVED***')
        curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
        curl.perform()
        curl.close()

        # Load response from memory buffer as JSON object and get price
        symbolDetail = json.loads(response_buffer.getvalue().decode('UTF-8'))
        latestPrice = symbolDetail["latestPrice"]

        # Calculate gain/loss, format to percentage and add to dict
        gain = (latestPrice - price) / price * 100
        gain = str(round(gain, 2)) + '%'
        record["gain"] = gain

    # Write changes to file    
    with path.open("w") as file:
        json.dump(portfolio, file)

    return

# Process form data from HTTP POST and store as JSON
def processForm(message):
    # Split POST body from header
    payload = message.split("\r\n\r\n")[1]
    # Break parameters into list
    x = payload.split("&")
    newData = {}
    # Convert list to dict
    for item in x:
        key, value = item.split("=")
        # Cast values to correct data types
        try:
            value = int(value)
            newData[key]=value
        except ValueError:
            try:
                value = float(value)
                newData[key]=value
            except ValueError:
                newData[key]=value
    # TODO catch invalied stock symbols from datalist
    # Validate user data and return error messages
    if newData["price"] <= 0:
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head></head><body><p>Invalid price (negative).</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif not isinstance(newData.get("quantity"), int):
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head></head><body><p>Invalid data type. Quantity requires an integer.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif not isinstance(newData.get("price"), int) and not isinstance(newData.get("price"), float):
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head></head><body><p>Invalid data type. Price requires an integer or decimal.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    
    # Read existing portfolio into memory
    try:
        path = Path(__file__).with_name('portfolio.json')
        with path.open("r") as file:
            portfolio = json.load(file)
    # If portfolio doesn't exist, create it
    # TODO test with file deleted
    # TODO has problems when file exists but empty, needs [] to work
    except (OSError, ValueError):
        with path.open("w") as file:
            json.dump(newData, file)
            portfolio = json.load(file)

    # If symbol does not exist in list then append it
    if not any(record["symbol"] == newData["symbol"] for record in portfolio):
        portfolio.append(newData)
    else:
        for record in portfolio:
            # If symbol is at same price then update quantity
            if record["symbol"] == newData["symbol"] and record["price"] == newData["price"]:
                record["quantity"] += newData["quantity"]
                # Delete record when quantity reaches 0 or below
                if record["quantity"] <= 0:
                    portfolio.remove(record)    
                break
            # If symbol is at different price append if quantity is positive
            if not any(record["symbol"] == newData["symbol"] and record["price"] == newData["price"] for record in portfolio):
                if newData["quantity"] >= 1:
                    portfolio.append(newData)
                    break
    # Write results back to file
    with path.open("w") as file:
        json.dump(portfolio, file)
    #Calculate gain/loss for portfolio
    calcGains()
    # Refresh the portfolio after changes
    header, body = showPortfolio()

    return header, body


def makePlot(resource) :
    symbol = re.search(r'[A-Z]+', resource).group(0)

    # API call to retrieve symbol details
    response_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, False)
    curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/stock/' + symbol + '/chart/ytd?chartCloseOnly=true&token=***REMOVED***')
    curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
    curl.perform()
    curl.close()

    ytd = json.loads(response_buffer.getvalue().decode('UTF-8'))
    dates = []
    close = []
    # Extract dates and closing prices for plotting
    for item in ytd:
        dates.append(item["date"])
        close.append(item["close"])

    fig = px.line(x=dates, y=close, title=symbol + ' YTD closing prices')
    # TODO fix filepath and plot axis labels
    fig.write_image("plot.png")

    header, body = showStock()
        
    return header, body


# Present portfolio page
def showPortfolio() :
    print("Showing portfolio...")

    # Check to see if the symbols file exists, if not, retrieve
    if Path(__file__).with_name('cs.json').is_file():
        pass
    else:
        getSymbols()

    # Add portfolio.html to body
    path = Path(__file__).with_name('portfolio.html')
    with path.open("rb") as file:
        body = file.read()

    header = "HTTP/1.1 200 OK\r\n\r\n".encode()

    return header, body


# Plot stock graph
def showStock():
    print("Showing stock...")

    if Path(__file__).with_name('cs.json').is_file():
        pass
    else:
        getSymbols()

    # Add portfolio.html to body
    path = Path(__file__).with_name('stock.html')
    with path.open("rb") as file:
        body = file.read()

    header = "HTTP/1.1 200 OK\r\n\r\n".encode()

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