"use strict";

function mergeCells(data) {
	var lastGroupStart = 0;
	for (var i = 1; i < data.length; i++) {
		if (
				(data[i][0] !== data[lastGroupStart][0])
			|| (data[i][1] !== data[lastGroupStart][1])
			|| (data[i][2] !== data[lastGroupStart][2])
			|| (data[i][5] !== data[lastGroupStart][5])
			|| (data[i][7] !== data[lastGroupStart][7])) {
			
			if (lastGroupStart + 1 !== i) {
				$("#table").bootstrapTable('mergeCells', {index: lastGroupStart, field: 7, rowspan: i-lastGroupStart});
			}
			
			lastGroupStart = i;
		}
	}
}

function initTable() {
	$('#table').bootstrapTable();

	$.getJSON( "api.py" + window.location.search, function( data ) {
    	$('#table').bootstrapTable('load', {data: data});
    	mergeCells(data);
	});
}

initTable();
