"use strict";

function mergeCells(data) {
	var lastGroupStart = 0;
	for (var i = 1; i < data.length; i++) {
		if (
				(data[i][0] !== data[lastGroupStart][0])
			|| (data[i][1] !== data[lastGroupStart][1])
			|| (data[i][4] !== data[lastGroupStart][4])
			|| (data[i][6] !== data[lastGroupStart][6])) {
			console.log(i, lastGroupStart);
			
			if (lastGroupStart + 1 !== i) {
				$("#table").bootstrapTable('mergeCells', {index: lastGroupStart, field: 6, rowspan: i-lastGroupStart});
			}
			
			lastGroupStart = i;
		}
	}
}

function initTable() {
	$('#table').bootstrapTable();

	$.getJSON( "data.json", function( data ) {
    	$('#table').bootstrapTable('load', {data: data});
    	mergeCells(data);
	});
}

initTable();
