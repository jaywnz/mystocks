// 159.352 Assignment 1
// Author: JW

"use strict";

let select = document.getElementById("symbol");
let placeholder = document.createElement("option");
let table = document.getElementById("portfolio");

// Construct placeholder option for select dropdown
placeholder.text = "Select stock";
placeholder.disabled = true;
placeholder.selected = true;
select.appendChild(placeholder);

// // Construct first row of table with headers
// row = document.createElement("tr");
// symbolHead = document.createElement("th");
// quantityHead = document.createElement("th");
// priceHead = document.createElement("th");
// table.appendChild(row);
// row.appendChild(symbolHead);
// row.appendChild(quantityHead);
// row.appendChild(priceHead);

// // Create table from portfolio.json
// fetch("http://localhost:8080/portfolio.json")
//     .then(response => response.json())
//     .then(data => {
//         let cell;
//         for (let j = 0; j < data.length; j++){
//             cell = document.createElement("td")



//         }
        
//     });

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