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
		vars[key] = decodeURIComponent(value.replace("+", " "));
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
 * Is this a primary paramter or a sub-paramter of a selected parent?
 */
function isQueryParameterImportant(vars, key) {
	if (key === "hours") {
		if (vars["date"] !== "hours") {
			return false;
		}
	} else if (key === "mindate" || key === "maxdate") {
		if (vars["date"] !== "explicit") {
			return false;
		}
	} 	
	return true;
}

function renderQueryParameters() {
	$(".search-parameter").each(function() {
		var params = ["Repository", "When", "Who", "Directory", "File", "Rev", "Branch", "Description", "Date", "Hours", "MinDate", "MaxDate"];
		var text = "";
		var vars = getUrlVars();
		for (var i = 0; i < params.length; i++) {
			var key = params[i].toLowerCase();

			if (!isQueryParameterImportant(vars, key)) {
				continue;
			}

			var value = vars[key];
			var type = vars[key + "type"];
			if (!value) {
				continue;
			}
			if (text.length > 0) {
				text = text + ", ";
			}
			var operator = "=";
			if (type === "regexp") {
				operator = "~";
			} else if (type === "notregexp") {
				operator = "!~";
			}
			text = text + params[i] + " " + operator + " " + value;
		}
		$(this).text(text);
	});
}

/**
 * hides redundant columns to preserve space
 */
function hideRedundantColumns() {
	var vars = getUrlVars();
	if (vars["branch"]) {
		$('#table').bootstrapTable('hideColumn', '5');
	}
	if (vars["repository"]) {
		$('#table').bootstrapTable('hideColumn', '0');
	}
}


/**
 * loads the search result from the server
 */
function initTable() {
	$('#table').bootstrapTable();

	$.getJSON( "api.py" + window.location.search, function( data ) {
		if (typeof data === "string") {
			alert(data);
			return;
		}
    	$('#table').bootstrapTable('load', {data: data});
		hideRedundantColumns();
    	mergeCells(data);
	});
}



$("ready", function() {
	addQueryStringToLink();
	addValuesFromURLs();
	if (document.querySelector("body.page-searchresult")) {
		renderQueryParameters();
		initTable();
	}
});
}());