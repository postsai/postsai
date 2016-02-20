(function() {

"use strict";

/**
 * merges commit messages on files commited together
 */
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

/**
 * rewrites the links to include the query string
 */
function addQueryStringToLink() {
	$(".action-add-querystring").each(function() {
		var href = this.href;
		if (href.indexOf("?") < 0) {
			$(this).attr("href", this.href + window.location.search);
		}
	});
}

/**
 * extracts parameters from query string
 */
// http://stackoverflow.com/a/20097994
function getUrlVars() {
	var vars = {};
	var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi,    
	function(m,key,value) {
		vars[key] = decodeURIComponent(value);
	});
	return vars;
}

/**
 * loads URL parameters into search form
 */
function addValuesFromURLs() {
	var params = getUrlVars();
	$("input").each(function() {
		var value = params[this.name];
		if (!value) {
			return;
		}

		if (this.type === "radio") {
			if (this.value === value) {
				$(this).attr("checked", true);
			}
		} else {
			$(this).val(value);
		}
	});
}

/**
 * loads the search result from the server
 */
function initTable() {
	$('#table').bootstrapTable();

	$.getJSON( "api.py" + window.location.search, function( data ) {
    	$('#table').bootstrapTable('load', {data: data});
    	mergeCells(data);
	});
}



$("ready", function() {
	addQueryStringToLink();
	addValuesFromURLs();
	if (document.querySelector("body.page-searchresult")) {
		initTable();
	}
});
}());