// 159.352 Assignment 1
// Author: JW

"use strict";

// Construct portfolio table
function makeTable() {
    let table = document.getElementById("portfolio");
    let currency = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    })
    // Construct first row of table with headers
    let row = document.createElement("tr");
    let stockHead = document.createElement("th");
    let quantityHead = document.createElement("th");
    let priceHead = document.createElement("th");
    let gainHead = document.createElement("th");
    stockHead.innerHTML = "Stock";
    quantityHead.innerHTML = "Quantity";
    priceHead.innerHTML = "Avg. Buy Price";
    gainHead.innerHTML = "Gain/Loss";
    table.appendChild(row);
    row.appendChild(stockHead);
    row.appendChild(quantityHead);
    row.appendChild(priceHead);
    row.appendChild(gainHead);

    // Create table from portfolio.json
    fetch("./public/portfolio.json")
        .then(response => response.json())
        .then(data => {
            for (let j = 0; j < data.length; j++){
                let row2 = document.createElement("tr");
                let cell1 = document.createElement("td");
                let cell2 = document.createElement("td");
                let cell3 = document.createElement("td");
                let cell4 = document.createElement("td");
                
                cell1.innerHTML = data[j].symbol;
                cell2.innerHTML = data[j].quantity;
                // Style price to USD for US stocks
                cell3.innerHTML = currency.format(data[j].average);
                cell4.innerHTML = data[j].gain;

                table.appendChild(row2);
                row2.appendChild(cell1);
                row2.appendChild(cell2);
                row2.appendChild(cell3);
                row2.appendChild(cell4);
            }

        });
}


// Create dropdown of stock symbols
function listSymbols() {
    let select = document.getElementById("symbol");
    let placeholder = document.createElement("option");

    // Construct placeholder option for select dropdown
    placeholder.text = "Select stock";
    placeholder.disabled = true;
    placeholder.selected = true;
    select.appendChild(placeholder);

    // Populate select with stock symbols from cs.json
    fetch("./public/cs.json")
    .then(response => response.json())
    .then(data => {
        let opt;
        for (let i = 0; i < data.length; i++){
            opt = document.createElement("option");
            opt.text = data[i].symbol;
            opt.value = data[i].symbol;
            select.appendChild(opt)
        }
    });
}


// Display generated stock plot
function showPlot() {
    let plotContainer = document.getElementById("plot");
    let plot = new Image();

    fetch("./img/plot.png")
    .then(function(response) {
        plot.src = "./img/plot.png"
        plotContainer.appendChild(plot)
     })

    // Test whether plot exists, if so replace, if not serve placeholder
    // fetch("./img/plot.png")
    // .then(function(response) {
    //     if (response.ok) {
    //         plot.src = "./img/plot.png"
    //         plotContainer.appendChild(plot)
    //     } else {
    //         plot.src = "./img/placeholder.png"
    //         plotContainer.appendChild(plot)
    //     }
    // })
}


// Convert POST payload into GET URL parameters
// Workaround for Heroku intermittent POST issue
// Adapted from https://stackoverflow.com/a/4726868
function doGet() {
    let form = document.getElementById("updateForm");
    let elements = form.elements;
    let values = [];

    //Only take first three values, 4th and 5th are buttons
    for (let k = 0; k < 3; k++){
        values.push(encodeURIComponent(elements[k].name) + "=" + encodeURIComponent(elements[k].value));
    }

    form.action += "?" + values.join("&");
}

if (document.getElementById("portfolio")){
    window.onload = makeTable();
    window.onload = listSymbols();
}
else {
    window.onload = showPlot();
    window.onload = listSymbols();
}
