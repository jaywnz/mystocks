# 159.352 Assignment 1
# MyStocks application without frameworks
# Author: JW

# api_calls.py: functions that make external API calls

import json
import re
import plotly.express as px
import urllib.request
from io import BytesIO


# Retrieve list of stock symbols from IEX Cloud as cs.json
def getSymbols():

    response_buffer = BytesIO()
    url = "https://cloud.iexapis.com/stable/ref-data/symbols?filter=symbol,type&token=pk_dc1d04cb0f2c4bc5b81af61256b2fd47"
    with urllib.request.urlopen(url) as response:
        response_buffer = response.read()
    # Load all symbols into JSON object from memory buffer
    allSymbols = json.loads(response_buffer.decode('UTF-8'))
    # Filter only those symbols of type 'cs'
    csSymbols = [x for x in allSymbols if x['type'] == 'cs']
    # Save filtered symbols to same directory as Python script
    path = "./public/cs.json"
    with open(path, "w") as file:
        json.dump(csSymbols, file)

    return


# Calculate the loss/gain percentage in reference to latest stock price
def calcGains(newData):
   
    symbol = newData["symbol"]
    avgPrice = newData["average"]

    response_buffer = BytesIO()
    url = "https://cloud.iexapis.com/stable/stock/" + symbol + "/quote?filter=symbol,latestPrice&token=pk_dc1d04cb0f2c4bc5b81af61256b2fd47"
    with urllib.request.urlopen(url) as response:
        response_buffer = response.read()
    # Load response from memory buffer as JSON object and get price
    symbolDetail = json.loads(response_buffer.decode('UTF-8'))
    latestPrice = symbolDetail["latestPrice"]
    # Calculate gain/loss, format to percentage and return
    gain = (latestPrice - avgPrice) / avgPrice * 100
    gain = str(round(gain, 2)) + '%'
    newData["gain"] = gain

    return newData
    
    # path = "./public/portfolio.json"
    # with open(path, "r") as file:
    #     portfolio = json.load(file)
    # # Extract symbol and average for each stock holding
    # for record in portfolio:
    #     symbol = record["symbol"]
    #     avgPrice = record["average"]
    #     # API call to retrieve latest price for symbol
    #     response_buffer = BytesIO()
    #     url = "https://cloud.iexapis.com/stable/stock/" + symbol + "/quote?filter=symbol,latestPrice&token=pk_dc1d04cb0f2c4bc5b81af61256b2fd47"
    #     with urllib.request.urlopen(url) as response:
    #         response_buffer = response.read()
    #     # Load response from memory buffer as JSON object and get price
    #     symbolDetail = json.loads(response_buffer.decode('UTF-8'))
    #     latestPrice = symbolDetail["latestPrice"]
    #     # Calculate gain/loss, format to percentage and update record
    #     gain = (latestPrice - avgPrice) / avgPrice * 100
    #     gain = str(round(gain, 2)) + '%'
    #     record["gain"] = gain
    # # Write changes to file
    # with open(path, "w") as file:
    #     json.dump(portfolio, file)


def getPlotData (symbol):

    response_buffer = BytesIO()
    url = "https://cloud.iexapis.com/stable/stock/" + symbol + "/chart/ytd?filter=date,close&chartCloseOnly=true&token=pk_dc1d04cb0f2c4bc5b81af61256b2fd47"
    with urllib.request.urlopen(url) as response:
        response_buffer = response.read()
    ytd = json.loads(response_buffer.decode('UTF-8'))

    # r = requests.get("https://cloud.iexapis.com/stable/stock/" + symbol + "/chart/ytd?filter=date,close&chartCloseOnly=true&token=pk_dc1d04cb0f2c4bc5b81af61256b2fd47")
    # ytd = r.json()

    return ytd
