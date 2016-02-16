function initTable() {
	$('#table').bootstrapTable();

	$.getJSON( "data.json", function( data ) {
    	$('#table').bootstrapTable('load', {data: data});
    	
	});
}

initTable();
