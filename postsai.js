(function() {

"use strict";

/**
 * merges commit messages on files committed together
 */
function mergeCells(data) {
	var lastGroupStart = 0;
	for (var i = 1; i < data.length; i++) {
		if (
				(data[i][0] !== data[lastGroupStart][0])
			|| (data[i][1].substring(0, 10) !== data[lastGroupStart][1].substring(0, 10))
			|| (data[i][2] !== data[lastGroupStart][2])
			|| (data[i][5] !== data[lastGroupStart][5])
			|| (data[i][7] !== data[lastGroupStart][7])) {
			
			if (lastGroupStart + 1 !== i) {
				$("#table").bootstrapTable('mergeCells', {index: lastGroupStart, field: 7, rowspan: i-lastGroupStart});
			}
			
			lastGroupStart = i;
		}
	}
	i = data.length - 1;
	if (
			(data[i][0] === data[lastGroupStart][0])
		&& (data[i][1].substring(0, 10) === data[lastGroupStart][1].substring(0, 10))
		&& (data[i][2] === data[lastGroupStart][2])
		&& (data[i][5] === data[lastGroupStart][5])
		&& (data[i][7] === data[lastGroupStart][7])) {
		
		if (lastGroupStart !== i) {
			$("#table").bootstrapTable('mergeCells', {index: lastGroupStart, field: 7, rowspan: i-lastGroupStart + 1});
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
	if (vars["branch"] && vars["branchtype"] === "match") {
		$('th[data-field="5"').remove();
//		$('#table').bootstrapTable('hideColumn', '5');
	}
	if (vars["repository"] && vars["repositorytype"] === "match") {
		$('th[data-field="0"').remove();
//		$('#table').bootstrapTable('hideColumn', '0');
	}
}


/**
 * loads the search result from the server
 */
function initTable() {
	$.getJSON( "api.py" + window.location.search, function( data ) {
		if (typeof data === "string") {
			alert(data);
			return;
		}
		window.config = data.config;
		hideRedundantColumns();
		$('#table').bootstrapTable();
    	$('#table').bootstrapTable('load', {data: data.data});
    	mergeCells(data.data);
    	$('#table').removeClass("hidden")
    	$(".spinner").addClass("hidden")
	});
}

$("ready", function() {
	window.config = {};
	addQueryStringToLink();
	addValuesFromURLs();
	if (document.querySelector("body.page-searchresult")) {
		renderQueryParameters();
		initTable();
	}
});
}());

// http://stackoverflow.com/a/12034334
var entityMap = {
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	'"': '&quot;',
	"'": '&#39;'
};
function escapeHtml(string) {
	return String(string).replace(/[&<>"']/g, function (s) {
		return entityMap[s];
	});
}
	
function formatTimestamp(value, row, index) {
	if (!value) {
		return "-";
	}
	return escapeHtml(value.substring(0, 16))
}

/**
 * formats the description column to link to an issue tracker
 */
function formatTrackerLink(value, row, index) {
	if (!value) {
		return "-";
	}
	var res = escapeHtml(value)
	if (!window.config.tracker) {
		return res;
	}
	return res.replace(/#([0-9][0-9][0-9][0-9][0-9]*)/g, 
		"<a href='" + window.config.tracker + "$1'>#$1</a>")
}

/**
 * formats the file column to link to viewvc file log
 */
function formatFileLink(value, row, index) {
	if (!value) {
		return "-";
	}
	var res = escapeHtml(value)
	if (!window.config.viewvc) {
		return res;
	}
	var repository = escapeHtml(row[0].replace("/srv/cvs/", "").replace("/var/lib/cvs/"));
	return "<a href='" + window.config.viewvc + "/" + repository + "/" + res +"'>" + res + "</a>";
}

/**
 * formats the rev column to link to viewvc file content
 */
function formatRevLink(value, row, index) {
	if (!value) {
		return "-";
	}
	var res = escapeHtml(value)
	if (!window.config.viewvc) {
		return res;
	}
	var repository = escapeHtml(row[0].replace("/srv/cvs/", "").replace("/var/lib/cvs/"));
	var file = escapeHtml(row[3]);
	return "<a href='" + window.config.viewvc + "/" + repository + "/" + file + "?revision=" 
		+ res + "&view=markup'>" + res + "</a>";
}

/**
 * format the diff column to link to the difference
 */
function formatDiffLink(value, row, index) {
	if (!value) {
		return "-";
	}
	var res = escapeHtml(value)
	if (!window.config.viewvc) {
		return res;
	}
	
	var file = escapeHtml(row[3]);
	var repository = escapeHtml(row[0].replace("/srv/cvs/", "").replace("/var/lib/cvs/"));
	var ref = escapeHtml(row[4])
	var pre = ref;
	
	// calculate previous revision number
	var split = ref.split(".");
	var last = split[split.length - 1];
	if (last === "1" && split.length > 2) {
		split.pop();
		split.pop();
	} else {
		split[split.length - 1] = parseInt(last) - 1;
	}
	pre = split.join(".");
	
	var diff = "?r1=" + pre + "&r2=" + ref;
	return "<a href='" + window.config.viewvc + "/" + repository + "/" + file + diff +"'>" + res + "</a>";
}

