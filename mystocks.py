# 159.352 Assignment 1
# MyStocks application without frameworks
# Author: JW, based on server3.py by Sunil Lal

from socket import *
from base64 import b64encode
from api_calls import *
import os
import _thread
import json
import re
import sys

# Set up socket and start listening
serverSocket = socket(AF_INET, SOCK_STREAM)
# serverPort = int(sys.argv[1])
serverPort = 8080
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(("", serverPort))
serverSocket.listen(5)
print('The server is running.')
sys.stdout.flush()


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
        with open(filename, "rb") as file:
            body = file.read()

        # Set correct headers per filetype
        if filename.endswith(('png', 'jpg')):
            contentType = "image/" + filename.split('.')[-1]
            cacheControl = "public"
        elif filename.endswith(('json')):
            contentType = "application/json"
            cacheControl = "public"
        elif filename.endswith(('css')):
            contentType = "text/css"
            cacheControl = "public, max-age=31536000"
        elif filename.endswith(('js')):
            contentType = "text/javascript"
            cacheControl = "public, max-age=31536000"
        else:
            contentType = "text/html"
            cacheControl = "public"

        header = ("HTTP/1.1 200 OK\r\nContent-Type:" +
                  contentType + "\r\nCache-Control:" + cacheControl + "\r\n\r\n").encode()

    except OSError:
        # Send HTTP response message for resource not found
        header = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><h1>404 Not Found</h1><ul><li><a href='/portfolio'>Portfolio</a></li><li><a href='/stock'>Stock Charts</a></li></ul></body></html>\r\n".encode()

    return header, body


# Serve a simple homepage
def home():

    header = "HTTP/1.1 200 OK\r\n\r\n".encode()
    body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><h1>Welcome to MyStocks</h1><ul><li><a href='/portfolio'>Portfolio</a></li><li><a href='/stock'>Stock Charts</a></li></ul></body></html>\r\n".encode()

    return header, body


# Process the client's request
def process(connectionSocket):

    # Declaring empty reponse strings prevents error on Heroku with intermittent empty request errors when app is idle
    responseHeader = b""
    responseBody = b""
    # Receives the request message from the client
    message = connectionSocket.recv(1024).decode()
    # Extract HTTP method
    method = getMethod(message)

    if len(message) > 1:
        # Extract the path of the requested object from the message
        resource = message.split()[1][1:]
        # Use regex to extract symbol from URL query if present
        # Only stock chart form uses GET method URL queries
        query = re.search(r'mystocks\.py\?symbol\=[A-Z]+', resource)
        # Catch unauthenticated users and send to login
        if getHeader(message, "Authorization") == None:
            responseHeader, responseBody = login(message)
        # Check is authorisation header is correct
        elif checkCredentials(message):
            # Only the portfolio form uses POST on the app
            # NOTE: Heroku requires parameters also to be passed as GET to avoid the intermittent POST failure issue, see doGet() JS function
            if method == "POST":
            # Append message to logfile for error checking
                with open("./logs.txt", "w") as file:
                    file.write(message)
                responseHeader, responseBody = processForm(message)
            elif query is not None:
                responseHeader, responseBody = makePlot(resource)
            elif resource == "portfolio":
                responseHeader, responseBody = showPortfolio()
            elif resource == "stock":
                responseHeader, responseBody = showStock()
            elif resource == "" or resource == "mystocks.py" or resource == "/":
                responseHeader, responseBody = home()
            else:
                responseHeader, responseBody = getFile(resource)
        # In case of login failure
        else:
            print("Invalid credentials.")
            sys.stdout.flush()
            responseHeader = "HTTP/1.1 403 Forbidden\r\n\r\n".encode()
            responseBody = "<html><head><title>MyStocks</title></head><body><h1>Invalid login</h1><p>Please enter the correct credentials to access this site.</p></body></html>\r\n".encode()

    # Send the HTTP response header line to the connection socket
    connectionSocket.send(responseHeader)
    # Send the content of the HTTP body to the connection socket
    connectionSocket.send(responseBody)
    connectionSocket.shutdown(SHUT_RDWR)
    # Close the client connection socket
    connectionSocket.close()


# Split message and return HTTP method
def getMethod(message):

    x = message.split(" ")
    method = x[0]

    return method


# Carry out basic HTTP authentication
def login(message):

    print("Authorising client.")
    sys.stdout.flush()
    header = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Please enter your credentials.\", charset=\"UTF-8\"\r\n\r\n".encode()
    body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><h1>Login</h1><p>Please enter your credentials to access this site.</p></body></html>\r\n".encode()
    return header, body

# Ensures correct login credentials
def checkCredentials(message):

    # Assumes only one user with fixed credentials
    serverCreds = b64encode(b"20020003:20020003").decode()
    if getHeader(message, "Authorization") == serverCreds:
        return 1
    else:
        return 0

    # elif getHeader(message, "Authorization") == serverCreds:
    #     print("User logged in.")
    #     sys.stdout.flush()
    #     header = "HTTP/1.1 200 OK\r\n\r\n".encode()
    #     body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><h1>Welcome to MyStocks!</h1><p>User logged in.</p><ul><li><a href='/portfolio'>Portfolio</a></li><li><a href='/stock'>Stock Charts</a></li></ul></body></html>\r\n".encode()
    #     # Set user authentication
    #     global auth
    #     auth = True
    #     return header, body
    # else:
    #     print("Invalid credentials.")
    #     sys.stdout.flush()
    #     header = "HTTP/1.1 403 Forbidden\r\n\r\n".encode()
    #     body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><h1>Invalid login</h1><p>Please enter the correct credentials to access this site.</p></body></html>\r\n".encode()
    #     return header, body


# Process form data from HTTP POST and store as JSON
# NOTE: Data taken from URL parameters in case of POST failure
def processForm(message):

    try:
        # Split POST body from header
        payload = message.split("\r\n\r\n")[1]
        # POST payload is present, process from body
        if payload != None or payload != "":
            # Break parameters into list
            x = payload.split("&")
            newData = {}
            print("Parsing POST...")
            sys.stdout.flush()
            # Convert list to dict
            for item in x:
                try:
                    key, value = item.split("=")
                except:
                    return
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
    except:
        print("POST failure, trying URL parameters...")
        sys.stdout.flush()
        # In the case of POST failure, retrieve data from URL parameters
        parameters = message.split("?")
        parameters = parameters[1].split(" ")
        payload = parameters[0]

        x = payload.split("&")
        newData = {}
        # Convert list to dict
        for item in x:
            try:
                key, value = item.split("=")
            except:
                return
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
    # A returned header and body means a validation error
    if (header and body):
        return header, body

    # Read existing portfolio into memory
    try:
        path = "./public/portfolio.json"
        with open(path, "r") as file:
            portfolio = json.load(file)
    # If portfolio doesn't exist, create it
    # TODO has problems when file exists but empty, needs [] to work
    except (OSError, ValueError):
        with open(path, "w") as file:
            json.dump(newData, file)
            portfolio = json.load(file)

    # If symbol does not exist in list then append it if quantity positive
    if newData["quantity"] > 0:
        if not any(record["symbol"] == newData["symbol"] for record in portfolio):
            newData["count"] = 1
            newData["average"] = float(newData["price"])

            # Calculate loss/gain on purchase
            newData = calcGains(newData)
            # Write changes to file
            portfolio.append(newData)
            with open(path, "w") as file:
                json.dump(portfolio, file)

            header, body = showPortfolio()
            return header, body

    # Check if user has submitted a negative quantity and reduce/remove stock
    # Do not recalculate average buy price based on negative quantity change
    if newData["quantity"] < 0:
        # If user has submitted non-existent symbol
        if not any(record["symbol"] == newData["symbol"] for record in portfolio):
            header = "HTTP/1.1 200 OK\r\n\r\n".encode()
            body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: You entered a negative quantity for a stock which you do not own.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
            return header, body
        else:
            for record in portfolio:
                if record["symbol"] == newData["symbol"]:
                    record["quantity"] += newData["quantity"]
                    if record["quantity"] <= 0:
                        portfolio.remove(record)
                    with open(path, "w") as file:
                        json.dump(portfolio, file)
                    break
    else:
        for record in portfolio:
            if record["symbol"] == newData["symbol"]:
                record["quantity"] += newData["quantity"]
                # Write changes to file
                with open(path, "w") as file:
                    json.dump(portfolio, file)
                break
        # Calculate moving average buy price for additional stock purchases
        calcMovingAvg(newData)
        # Deleted calcGains() call for speed. Loss/gain updated on first entry to portfolio

    # Refresh the portfolio after changes
    header, body = showPortfolio()

    return header, body


# Server-side validation of client data
def formValidate(newData):

    # Check for nulls first to avoid iteration errors
    if newData.get("symbol") == None:
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: You did not enter a stock symbol.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif newData["quantity"] == "" and newData["price"] == "":
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: You did not enter a quantity or price.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif newData["quantity"] == "":
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: You did not enter a quantity.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # After dealing with nulls, check if the user is reducing stock
    elif newData["quantity"] < 0:
        # Set price to zero to avoid errors
        newData["price"] = 0
        return 0, 0
    # Catch last remaining null
    elif newData["price"] == "":
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: You did not enter a price.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # Catch zeros
    elif newData["quantity"] == 0 or newData["price"] == 0:
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: You entered a zero quantity or price.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # Catch negative prices
    elif newData["price"] < 0:
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: You entered a negative price. If you would like to reduce/remove a stock, please enter a negative quantity.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    # Catch invalid data types for quantity and price
    # Should be caught client-side, but provides extra protection
    elif not isinstance(newData.get("quantity"), int):
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: Invalid data type. Quantity requires an integer.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    elif not isinstance(newData.get("price"), int) and not isinstance(newData.get("price"), float):
        header = "HTTP/1.1 200 OK\r\n\r\n".encode()
        body = "<html><head><title>MyStocks</title><link rel='stylesheet' href='main.css'></head><body><p>Error: Invalid data type. Price requires an integer or decimal.</p><a href='/portfolio'>Go back to portfolio</a>.</body></html>\r\n".encode()
        return header, body
    else:
        return 0, 0


# Calculate the moving average of a stock price
def calcMovingAvg(newData):

    path = "./public/portfolio.json"
    with open(path, "r") as file:
        portfolio = json.load(file)

    for record in portfolio:
        if record["symbol"] == newData["symbol"]:
            if record["average"] == 0.0:
                # Set price to average if first transaction in a stock
                record["average"] = record["price"]
                break
            else:
                # Use count to calculate moving average and update record
                record["count"] += 1
                newAvg = (record["average"] * (record["count"] -
                          1) + newData["price"]) / record["count"]
                record["average"] = newAvg
                break
            # # Adjust stock quantities and if it falls below zero, remove
            # record["quantity"] += newData["quantity"]
            # if record["quantity"] <= 0:
            #     portfolio.remove(record)
            #     break
    # Write changes to file
    with open(path, "w") as file:
        json.dump(portfolio, file)

    return


def makePlot(resource):

    # Use regex to extract symbol name
    symbol = re.search(r'[A-Z]+', resource).group(0)

    # API call to retrieve symbol details
    ytd = getPlotData(symbol)
    dates = []
    close = []
    # Extract dates and closing prices for plotting
    for item in ytd:
        dates.append(item["date"])
        close.append(item["close"])
    # Create plot
    fig = px.line(x=dates, y=close, title=symbol + " closing prices YTD", template="ggplot2")
    fig.update_xaxes(title_text="2021")
    fig.update_yaxes(title_text="Closing Price (USD)")
    path = "./img/plot.png"
    fig.write_image(path)

    header, body = showStock()

    return header, body


# Present portfolio page
def showPortfolio():

    print("Showing portfolio...")
    sys.stdout.flush()
    # Check to see if the symbols file exists, if not, retrieve
    path = "./public/cs.json"
    if os.path.isfile(path):
        pass
    else:
        getSymbols()
    # Add portfolio.html to body
    # path = Path(__file__).with_name('portfolio.html')
    path = "./portfolio.html"
    with open(path, "rb") as file:
        body = file.read()
    header = "HTTP/1.1 200 OK\r\n\r\n".encode()

    return header, body


# Plot stock graph
def showStock():

    print("Showing stock...")
    sys.stdout.flush()
    # Check to see if the symbols file exists, if not, retrieve
    path = "./public/cs.json"
    if os.path.isfile(path):
        pass
    else:
        getSymbols()
    # Add stock.html to body
    # path = Path(__file__).with_name('stock.html')
    path = "./stock.html"
    with open(path, "rb") as file:
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
