// 159.352 Assignment 1
// Author: JW

"use strict";

var select = document.getElementById("symbol");
var placeholder = document.createElement("option");
placeholder.text = "Select stock";
placeholder.disabled = true;
placeholder.selected = true;

select.appendChild(placeholder);

fetch("http://localhost:8080/cs.json")
    .then(response => response.json())
    .then(data => {
        var opt;
        for (var i = 0; i < data.length; i++){
            opt = document.createElement("option");
            opt.text = data[i].symbol;
            opt.value = data[i].symbol;
            select.appendChild(opt)
        }
    });