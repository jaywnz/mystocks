# 159.352 Assignment 1
# MyStocks application without frameworks
# Author: JW, based on server3.py by Sunil Lal

from socket import *
from base64 import b64encode
from io import BytesIO
from pathlib import Path
import _thread
import pycurl
import json
import plotly.express as px
import re
import sys

serverSocket = socket(AF_INET, SOCK_STREAM)

# serverPort = 8080
serverPort = int(sys.argv[1])
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


# Fetch the requested file and send the contents back to the client
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

        header = ("HTTP/1.1 200 OK\r\nContent-Type:" +
                  contentType + "\r\n\r\n").encode()

    except OSError:
        # Send HTTP response message for resource not found
        header = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><h1>404 Not Found</h1><ul><li><a href='/portfolio'>Portfolio</a></li><li><a href='/stock'>Stock Charts</a></li></ul></body></html>\r\n".encode()

    return header, body


# Serve a simple homepage
def home():

    header = "HTTP/1.1 200 OK\r\n\r\n".encode()
    body = "<html><head><title>MyStocks</title></head><body><h1>MyStocks</h1><ul><li><a href='/portfolio'>Portfolio</a></li><li><a href='/stock'>Stock Charts</a></li></ul></body></html>\r\n".encode()

    return header, body


# Process the client's request
def process(connectionSocket):

    # Receives the request message from the client
    message = connectionSocket.recv(1024).decode()
    # Extract HTTP method
    method = getMethod(message)
    # Only the portfolio form uses POST on the app
    if method == "POST":
        responseHeader, responseBody = processForm(message)
    elif len(message) > 1:
        # Extract the path of the requested object from the message
        resource = message.split()[1][1:]
        # Use regex to extract symbol from URL query if present
        # Only stock chart form uses GET method URL queries
        query = re.search(r'mystocks\.py\?symbol\=[A-Z]+', resource)
        if auth == False:
            responseHeader, responseBody = authenticate(message)
        else:
            if query is not None:
                responseHeader, responseBody = makePlot(resource)
            elif resource == "portfolio":
                responseHeader, responseBody = showPortfolio()
            elif resource == "stock":
                responseHeader, responseBody = showStock()
            elif resource == "" or resource == "mystocks.py":
                responseHeader, responseBody = home()
            else:
                responseHeader, responseBody = getFile(resource)
    # Send the HTTP response header line to the connection socket
    connectionSocket.send(responseHeader)
    # Send the content of the HTTP body to the connection socket
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

    # Assumes only one user with fixed credentials
    serverCreds = b64encode(b"***REMOVED***:***REMOVED***").decode()
    if getHeader(message, "Authorization") == None:
        print("Authorising client.")
        header = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Please enter your credentials.\", charset=\"UTF-8\"\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><h1>Login</h1><p>Please enter your credentials to access this site.</p></body></html>\r\n".encode()
        return header, body
    elif getHeader(message, "Authorization") == serverCreds:
        print("User logged in.")
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><h1>Welcome to MyStocks!</h1><p>User logged in.</p><ul><li><a href='/portfolio'>Portfolio</a></li><li><a href='/stock'>Stock Charts</a></li></ul></body></html>\r\n".encode()
        # Set user authentication
        global auth
        auth = True
        return header, body
    else:
        print("Invalid credentials.")
        header = "HTTP/1.1 403 Forbidden\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><h1>Invalid login</h1><p>Please enter the correct credentials to access this site.</p></body></html>\r\n".encode()
        return header, body


# Retrieve list of stock symbols from IEX Cloud as cs.json
def getSymbols():
    response_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, False)
    curl.setopt(
        curl.URL, 'https://cloud.iexapis.com/stable/ref-data/symbols?token=***REMOVED***')
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
            newData[key] = value
        except ValueError:
            try:
                value = float(value)
                newData[key] = value
            except ValueError:
                newData[key] = value

    # Send user data off for validation
    header, body = formValidate(newData)
    if (header and body):
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

    # If symbol does not exist in list then append it if quantity positive
    if newData["quantity"] > 0:
        if not any(record["symbol"] == newData["symbol"] for record in portfolio):
            newData["count"] = 1
            newData["average"] = float(newData["price"])
            portfolio.append(newData)
            with path.open("w") as file:
                json.dump(portfolio, file)
            calcGains()
    # Check if user has submitted a negative quantity and reduce/remove stock
    # Do not recalculate average buy price based on negative quantity change
    if newData["quantity"] < 0:
        # If user has submitted non-existent symbol
        if not any(record["symbol"] == newData["symbol"] for record in portfolio):
            header = "HTTP/1.1 200 OK\r\n\r\n".encode()
            body = "<html><head><title>MyStocks</title></head><body><p>Error: You entered a negative quantity for a stock which you do not own.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
            return header, body
        else:
            for record in portfolio:
                if record["symbol"] == newData["symbol"]:
                    record["quantity"] += newData["quantity"]
                    if record["quantity"] <= 0:
                        portfolio.remove(record)
                    with path.open("w") as file:
                        json.dump(portfolio, file)
                    break
    else:
        for record in portfolio:
            if record["symbol"] == newData["symbol"]:
                record["quantity"] += newData["quantity"]
                break
        calcMovingAvg(newData)
        # TODO does it twice for an addition to an existing symbol
        calcGains()

    # Refresh the portfolio after changes
    header, body = showPortfolio()

    return header, body


# Server-side validation of client data
def formValidate(newData):

    # Check for nulls first to avoid iteration errors
    if newData.get("symbol") == None:
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: You did not enter a stock symbol.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif newData["quantity"] == "" and newData["price"] == "":
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: You did not enter a quantity or price.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif newData["quantity"] == "":
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: You did not enter a quantity.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # After dealing with nulls, check if the user is reducing stock
    elif newData["quantity"] < 0:
        # Set price to zero to avoid errors
        newData["price"] = 0
        return 0, 0
    # Catch last remaining null
    elif newData["price"] == "":
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: You did not enter a price.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # Catch zeros
    elif newData["quantity"] == 0 or newData["price"] == 0:
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: You entered a zero quantity or price.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # Catch negative prices
    elif newData["price"] < 0:
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: You entered a negative price. If you would like to reduce/remove a stock, please enter a negative quantity.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # Catch invalid data types for quantity and price
    # Should be caught client-side, but provides extra protection
    elif not isinstance(newData.get("quantity"), int):
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: Invalid data type. Quantity requires an integer.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif not isinstance(newData.get("price"), int) and not isinstance(newData.get("price"), float):
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title></head><body><p>Error: Invalid data type. Price requires an integer or decimal.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    else:
        return 0, 0


# Calculate the moving average of a stock price
def calcMovingAvg(newData):

    path = Path(__file__).with_name('portfolio.json')
    with path.open("r") as file:
        portfolio = json.load(file)
    for record in portfolio:
        if record["symbol"] == newData["symbol"]:
            if record["average"] == 0.0:
                # Set price to average if first transaction in a stock
                record["average"] = record["price"]
            else:
                # Use count to calculate moving average and update record
                record["count"] += 1
                newAvg = (record["average"] * (record["count"] -
                          1) + newData["price"]) / record["count"]
                record["average"] = newAvg
            # Adjust stock quantities and if it falls below zero, remove
            record["quantity"] += newData["quantity"]
            if record["quantity"] <= 0:
                portfolio.remove(record)
                break
    # Write changes to file
    with path.open("w") as file:
        json.dump(portfolio, file)

    return


# Calculate the loss/gain percentage in reference to latest stock price
def calcGains():

    path = Path(__file__).with_name('portfolio.json')
    with path.open("r") as file:
        portfolio = json.load(file)
    # Extract symbol and average for each stock holding
    for record in portfolio:
        symbol = record["symbol"]
        avgPrice = record["average"]
        # API call to retrieve latest price for symbol
        response_buffer = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(curl.SSL_VERIFYPEER, False)
        curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/stock/' +
                    symbol + '/quote?token=***REMOVED***')
        curl.setopt(curl.WRITEFUNCTION, response_buffer.write)
        curl.perform()
        curl.close()
        # Load response from memory buffer as JSON object and get price
        symbolDetail = json.loads(response_buffer.getvalue().decode('UTF-8'))
        latestPrice = symbolDetail["latestPrice"]
        # Calculate gain/loss, format to percentage and update record
        gain = (latestPrice - avgPrice) / avgPrice * 100
        gain = str(round(gain, 2)) + '%'
        record["gain"] = gain
    # Write changes to file
    with path.open("w") as file:
        json.dump(portfolio, file)

    return


def makePlot(resource):

    # Use regex to extract symbol name
    symbol = re.search(r'[A-Z]+', resource).group(0)

    # API call to retrieve symbol details
    response_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, False)
    curl.setopt(curl.URL, 'https://cloud.iexapis.com/stable/stock/' + symbol +
                '/chart/ytd?chartCloseOnly=true&token=***REMOVED***')
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
    # Create plot
    fig = px.line(x=dates, y=close, title=symbol + ' YTD closing prices')
    # TODO fix plot axis labels
    # Set output path, convert to string and write image
    path = Path(__file__).with_name('plot.png')
    path = path.as_posix()
    fig.write_image(path)

    header, body = showStock()

    return header, body


# Present portfolio page
def showPortfolio():

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
    # Check to see if the symbols file exists, if not, retrieve
    if Path(__file__).with_name('cs.json').is_file():
        pass
    else:
        getSymbols()
    # Add stock.html to body
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
    _thread.start_new_thread(process, (connectionSocket,))
