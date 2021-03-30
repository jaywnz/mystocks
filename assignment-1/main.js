// 159.352 Assignment 1
// Author: JW

"use strict";

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
    fetch("http://localhost:8080/portfolio.json")
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

function listSymbols() {
    let select = document.getElementById("symbol");
    let placeholder = document.createElement("option");

    // Construct placeholder option for select dropdown
    placeholder.text = "Select stock";
    placeholder.disabled = true;
    placeholder.selected = true;
    select.appendChild(placeholder);

    // Populate select with stock symbols from cs.json
    fetch("http://localhost:8080/cs.json")
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

// function showPlot() {
//     let plotContainer = document.getElementById("plot");
//     let plot = new Image();
//     plot.src = "plot.png"
//     plotContainer.appendChild(plot)
// }

if (document.getElementById("portfolio")){
    window.onload = makeTable();
    window.onload = listSymbols();
}
else {
    window.onload = listSymbols();
}