# MyStocks Portfolio Tracker

MyStocks is a US stock portfolio tracker and plotting app built without the use of web frameworks. It relies on Python sockets and low-level HTTP request/response. MyStocks is deployed in a Docker container on Heroku. US stock market data is retrieved via the [IEX Cloud](https://www.iexcloud.io/) API.

Created as part of the Advanced Web Development course (159.352), semester 1, 2021, Massey University, New Zealand.

- [Base URL](https://mystocks-159352.herokuapp.com)
- [Portfolio](https://mystocks-159352.herokuapp.com/portfolio)
- [Stock Charts](https://mystocks-159352.herokuapp.com/stock)
- [Log](https://mystocks-159352.herokuapp.com/logs.txt)

## HTTP Authentication

Username: user  
Password: pass

## Known issues

Heroku intermittently drops POST payloads from form submissions on the portfolio page. A workaround is implemented whereby the HTTP method remains POST (as per the assignment brief), but the payload is appended in the URL by a JavaScript function `doGet()` which is used as a fallback in case of POST failure. This issue has been tested and replicated across Firefox/Chrome/Edge and via HTTP/HTTPS. The stock charts form submits as GET and is therefore not affected by this issue.

When running in a Docker container locally, the browser throws a JSON parse error on `cs.json` which results in the stock symbols dropdown not functioning. This is due to JavaScript fetch which requires the file to be served by a web server. This resolves when running on Heroku.