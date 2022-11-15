var $ = window.$ || {};
var hljs = window.hljs || {};

(function() {
"use strict";

var hashCache = {};

//http://stackoverflow.com/a/12034334
var entityMap = {
	"&": "&amp;",
	"<": "&lt;",
	">": "&gt;",
	"\"": "&quot;"
};
function escapeHtml(string) {
	return String(string).replace(/[&<>"]/g, function (s) {
		return entityMap[s];
	});
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
	window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi,
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
 * loads additional scripts
 *
 * @param scripts array of javascript filenames
 */
function loadAdditionalScripts(scripts) {
	for (var i = 0; i < scripts.length; i++) {
		var script = document.createElement('script');
		script.src = scripts[i];
		document.head.appendChild(script);
	}
}

/**
 * initializes a data list for auto complete
 */
function repositoryDatalist() {
	$.getJSON( "api.py?date=none", function( data ) {
		var list = [];
		for (var repo in data.repositories) {
			if (data.repositories.hasOwnProperty(repo)) {
				list.push(repo);
			}
		}

		list.sort();

		var temp = "";
		for (var i = 0; i < list.length; i++) {
			temp = temp + '<option value="' + escapeHtml(list[i]) + '">';
		}
		document.getElementById("repositorylist").innerHTML = temp;
		loadAdditionalScripts(data.additional_scripts);
	});
}

/**
 * Is this a primary paramter or a sub-paramter of a selected parent?
 */
function isQueryParameterImportant(vars, key) {
	if (key === "hours") {
		return (vars["date"] === "hours");
	} else if (key === "mindate" || key === "maxdate") {
		return (vars["date"] === "explicit");
	}
	return true;
}

/**
 * converts the operator parameter into a human readable form
 */
function typeToOperator(type) {
	var operator = "";
	if (type === "regexp") {
		operator = "~";
	} else if (type === "notregexp") {
		operator = "!~";
	}
	return operator;
}

/**
 * renders a summary of the search query
 */
function renderQueryParameters() {
	$(".search-parameter").each(function() {
		var params = ["Repository", "Branch", "When", "Who", "Dir", "File", "Rev", "Description", "Commit", "Forked_from", "Date", "Hours", "MinDate", "MaxDate"];
		var text = "";
		var title = "";
		var vars = getUrlVars();
		for (var i = 0; i < params.length; i++) {
			var key = params[i].toLowerCase();
			if (!isQueryParameterImportant(vars, key)) {
				continue;
			}
			var value = vars[key];
			if (!value) {
				continue;
			}
			if (text.length > 0) {
				text = text + ", ";
				title = title + ", ";
			}
			var type = vars[key + "type"];
			var operator = typeToOperator(type);
			text = text + params[i].replace("_", " ") + ": " + operator + " " + value;
			title = title + operator + " " + value;
		}
		$(this).text(text);
		$("title").text(title + " - Postsai");
	});
}

/**
 * hides redundant columns to preserve space
 */
function hideRedundantColumns() {
	var vars = getUrlVars();
	if (vars["branch"] && vars["branchtype"] === "match") {
		$("th[data-field='5'").remove();
//		$('#table').bootstrapTable("hideColumn", "5");
	}
	if (vars["repository"] && vars["repositorytype"] === "match") {
		$("th[data-field='0'").remove();
//		$('#table').bootstrapTable("hideColumn", "0");
	}
}

/**
 * renders the header of commits
 */
function renderCommitHeader(url, header) {
	var result = "<h2>Commit: " + escapeHtml(header.description) + "</h2>"
		+ "<b>by " + escapeHtml(header.author)
		+ " on "  + escapeHtml(header.timestamp) + ", "
		+ "<a href=\"" + escapeHtml(url + "&download=true") + "\">Download Patch</a></b><br>";
	return result;
}

/**
 * renders the diff of a commit
 */
function renderDiff(data) {
	var result = "<table class='diff'>";

	var start = data.indexOf("\n") + 1;
	var end = data.indexOf("\n", start);
	var firstChunkInFile = true;
	var filetype = "";
	while (end > -1) {
		var line = data.substring(start, end);
		var type = data.substring(start, start + 1);
		if (type === "I") {
			var file = line.substring(7);
			result += "<tr class='difffile'><td colspan='2'>" + escapeHtml(file) + "</td></tr>";
			filetype = file.substring(file.lastIndexOf(".") + 1, file.length);
			firstChunkInFile = true;

			// skip next three lines for non binary files
			var tmp = data.substring(end + 1, end + 6);
			if (tmp.length >= 5 && tmp !== "Index") {
				end = data.indexOf("\n", data.indexOf("\n", data.indexOf("\n", end + 1) + 1) + 1);
			}
		} else if (type === "+") {
			result += "<tr class='diffadd'><td class='diffsmall'>+</td><td class='" + filetype + " hilight'>" + escapeHtml(line.substring(1)) + "&nbsp;</td></tr>";
		} else if (type === "-") {
			result += "<tr class='diffdel'><td class='diffsmall'>-</td><td class='" + filetype + " hilight'>" + escapeHtml(line.substring(1)) + "&nbsp;</td></tr>";
		} else if (type === " ") {
			result += "<tr class='diffsta'><td class='diffsmall'>&nbsp;</td><td class='" + filetype + " hilight'>" + escapeHtml(line.substring(1)) + "&nbsp;</td></tr>";
		} else if (type === "@") {
			if (!firstChunkInFile) {
				result += "<tr class='diffsta'><td colspan='2'><hr></td></tr>";
			}
			firstChunkInFile = false;
		}
		start = end + 1;
		end = data.indexOf("\n", start);
	}

	result += "</table>";
	return result;
}

/**
 * loads the commit information from the server
 */
function renderCommit() {
	var prop = getUrlVars();
	var url = "api.py?method=commit&repository=" + prop["repository"] + " &commit=" + prop["commit"];
	$.ajax({
		url: url,
		success: function(data) {
			var header = JSON.parse(data.substring(1, data.indexOf("\n")));
			document.querySelector("div.contentplaceholder").innerHTML
				= renderCommitHeader(url, header)
				+ renderDiff(data);

			// start highlighting after giving a chance to breath
			window.setTimeout(function() {
				$('.hilight').each(function(i, block) {
					hljs.highlightBlock(block);
				});
			}, 1);
		},
		error: function(jqXHR, textStatus, errorThrown) {
			$("span.waitmessage").text("An error occurred on communication with the backend.");
		}
	});
}

function isCardView() {
	return $("#table").find('div.card-view').length > 0;
}

function guessSCM(revision) {
	if ((revision === "") || revision.indexOf(".") >= 0) {
		return "cvs";
	} else if (revision.length < 40) {
		return "subversion";
	}
	return "git";
}

function rowToProp(row) {
	var scm = guessSCM(row[4][0]);
	var commit = row[9];
	if (!commit) {
		commit = row[4][0];
	}
	var prop = {
		"[repository]": escapeHtml(row[0].replace("/srv/cvs/", "").replace("/var/lib/cvs/")),
		"[file]" : escapeHtml(row[3]),
		"[revision]": escapeHtml(row[4]),
		"[commit]": escapeHtml(commit),
		"[short_commit]": escapeHtml(commit),
		"[scm]": scm
	};
	if (scm === "cvs") {
		prop["[short_commit]"] = escapeHtml(commit.substring(commit.length - 8, commit.length));
	}
	if (scm === "git") {
		prop["[short_commit]"] = escapeHtml(commit.substring(0, 8));
	}
	return prop;
}

function argsubst(str, prop) {
	for (var key in prop) {
		if (prop.hasOwnProperty(key)) {
			var value = prop[key];
			while(str.indexOf(key) > -1) {
				str = str.replace(key, value);
			}
		}
	}
	return str;
}


function formatTimestamp(value, row, index) {
	if (!value) {
		return "-";
	}
	return escapeHtml(value.substring(0, 16));
}

function readRepositoryConfig(repo, key, fallback) {
	var repoConfig = window.repositories ? window.repositories[repo] : null;
	if (!repoConfig || !repoConfig[key]) {
		return fallback;
	}
	return (repoConfig[key] !== "") ? repoConfig[key] : fallback;
}

/**
 * formats the description column to link to an issue tracker
 */
function formatTrackerLink(value, row, index) {
	if (!value) {
		return "-";
	}
	var res = escapeHtml(value);
	var url = readRepositoryConfig(row[0], "tracker_url", window.config.tracker);
	if (!url) {
		return res;
	}

	return res.replace(/#([0-9]+)/g, '<a href="' + url + '">#$1</a>');
}


function formatFileLinkString(value, row, index) {
	var prop = rowToProp(row);
	var url = readRepositoryConfig(row[0], "file_url", null);
	if (!url) {
		return escapeHtml(value);
	}
	return argsubst('<a href="' + url + '">[file]</a>', prop);
}

function formatFileLinkArray(value, row, index) {
	var prop = rowToProp(row);
	var url = readRepositoryConfig(row[0], "file_url", null);

	if (value.length === 0) {
		return "-";
	}

	var res = [];
	for (var i = 0; i < value.length; i++) {
		if (!url) {
			res.push(escapeHtml(value[i]));
		} else {
			prop['[file]'] = value[i];
			prop['[revision]'] = row[4][i];
			res.push(argsubst('<a href="' + url + '">[file]</a>', prop));
		}
	}
	return "<ul class=\"filelist\"><li>" + res.join("<span class=\"hidden\">, </span><li>") + "</ul>";
}

function formatFileLink(value, row, index) {
	if (!value) {
		return "-";
	}
	if (value instanceof Array) {
		return formatFileLinkArray(value, row, index);
	} else {
		return formatFileLinkString(value, row, index);
	}
}


function formatDiffLink(value, row, index) {
	if (!value) {
		return "-";
	}
	var prop = rowToProp(row);
	var url = readRepositoryConfig(row[0], "commit_url", null);
	if (!url) {
		return prop["[short_commit]"];
	}
	return argsubst('<a href="' + url + '">[short_commit]</a>', prop);
}

function formatRepository(value, row, index) {
	var prop = rowToProp(row);
	var url = readRepositoryConfig(row[0], "icon_url", null);
	if (url) {
		return '<img src="' + argsubst(url, prop) + '" height="20px" width="20px"> ' + escapeHtml(value);
	}
	return escapeHtml(value);
}

function hashWithCache(input) {
	var hash = hashCache[input];
	if (!hash) {
		hash = window.md5(input);
		hashCache[input] = hash;
	}
	return hash;
}

function formatAuthor(value, row, index) {
	var icon = "";
	if (window.config.avatar) {
		icon = '<img src="' + window.config.avatar + '/avatar/' + window.md5(value) + '.jpg?s=20&amp;d=wavatar"> ';
	}
	var text = value;
	if (window.config.trim_email) {
		text = text.replace(/@.*/, "");
	}
    return icon + escapeHtml(text);
}

/**
 * enables or disables service worker based on config
 */
function setupServiceWorker() {
	if (window.config.service_worker === false) {
		if (navigator.serviceWorker) {
			// Disable service worker for now because of 
			// https://bugs.chromium.org/p/chromium/issues/detail?id=623464#
			// https://bugzilla.mozilla.org/show_bug.cgi?id=1291893
			navigator.serviceWorker.getRegistrations().then(function(registrations) {
				for(let registration of registrations) {
					registration.unregister();
				}
			});
		}
	} else {
		if (navigator.serviceWorker) {
			navigator.serviceWorker.register('service-worker.js');
		}
	}
}

/**
 * loads the search result from the server
 */
function initTable() {
	$.ajax({
		dataType: "json",
		url: "api.py" + window.location.search,
		success: function( data ) {
			if (typeof data === "string") {
				alert(data);
				return;
			}
			$("span.waitmessage").text("Please stand by while the browser is working.");
			window.config = data.config;
			window.repositories = data.repositories;
			loadAdditionalScripts(data.additional_scripts);
			setupServiceWorker();
			hideRedundantColumns();
			$("#table").bootstrapTable({
				onClickRow: function (row, $element) {
					// only react on clicks in the whole row if on mobile devices
					if (isCardView()) {
						var prop = rowToProp(row);
						var url = readRepositoryConfig(row[0], "commit_url", null);
						if (url) {
							var diffLink = argsubst(url, prop);
							window.document.location = diffLink;
						}
					}
				}
			});
			$("#table").bootstrapTable("load", {data: data.data});
			$("#table").removeClass("hidden");
			$(".spinner").addClass("hidden");
		},
		error: function(jqXHR, textStatus, errorThrown) {
			$("span.waitmessage").text("An error occurred on communication with the backend.");
		}
	});
}

function copyHandler(event) {
	let text = window.getSelection().toString().replace(/[\u200B-\u200D\uFEFF]/g, '');
	event.clipboardData.setData('text/plain', text);
	event.preventDefault();
}

// export functions
window["formatAuthor"] = formatAuthor;
window["formatFileLink"] = formatFileLink;
window["formatTimestamp"] = formatTimestamp;
window["formatTrackerLink"] = formatTrackerLink;
window["formatDiffLink"] = formatDiffLink;
window["formatRepository"] = formatRepository;

$("ready", function() {
	window.config = {};
	addQueryStringToLink();
	document.querySelector("body").addEventListener("copy", copyHandler);
	if (document.querySelector("body.page-searchresult")) {
		renderQueryParameters();
		initTable();
	} else if (document.querySelector("body.page-commit")) {
		renderCommit();
	} else {
		addValuesFromURLs();
		repositoryDatalist();
	}
});
}());
