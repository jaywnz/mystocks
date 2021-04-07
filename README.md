# MyStocks Portfolio Tracker

MyStocks is a US stock portfolio tracker and plotting app built without the use of web frameworks. It relies on Python sockets and HTTP requests/responses. MyStocks is deployed in a Docker container on Heroku. US stock market data is retrieved via the [IEX Cloud](https://www.iexcloud.io/) API.

Created as part of the Advanced Web Development course (159.352), semester 1, 2021, Massey University, New Zealand.

- [Base URL](https://mystocks-159352.herokuapp.com)
- [Portfolio](https://mystocks-159352.herokuapp.com/portfolio)
- [Stock Charts](https://mystocks-159352.herokuapp.com/stocks)
- [Log](https://mystocks-159352.herokuapp.com/logs.txt)

## Known issues

Heroku intermittently drops POST payloads from form submissions on the portfolio page. A workaround is implemented whereby the HTTP method remains POST, but the payload is appended in the URL by a JavaScript function which is used as a fallback in case of POST failure. This issue has been tested and replicated across Firefox/Chrome/Edge and via HTTP/HTTPS.

The stock charts form submits with GET and is therefore not affected by this issue.