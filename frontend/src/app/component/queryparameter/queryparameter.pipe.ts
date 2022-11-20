import { Pipe, PipeTransform } from '@angular/core';
import { Params } from '@angular/router';

@Pipe({
	name: 'queryparameter',
})
export class QueryParameterPipe implements PipeTransform {

	transform(vars?: Params, ..._args: any[]) {
		if (!vars) {
			return "";
		}

		let params = ["Repository", "Branch", "When", "Who", "Dir", "File", "Rev", "Description", "Commit", "Forked_from", "Date", "Hours", "MinDate", "MaxDate"];
		let text = "";
		let title = "";
		for (let i = 0; i < params.length; i++) {
			let key = params[i].toLowerCase();
			if (!this.isQueryParameterImportant(vars, key)) {
				continue;
			}
			let value = vars[key];
			if (!value) {
				continue;
			}
			if (text.length > 0) {
				text = text + ", ";
				title = title + ", ";
			}
			let type = vars[key + "type"];
			let operator = this.typeToOperator(type);
			text = text + params[i].replace("_", " ") + ": " + operator + " " + value;
			title = title + operator + " " + value;
		}
		
		// TODO:Change Window Title $("title").text(title + " - Postsai");
		return text;
	}

	/**
	 * Is this a primary paramter or a sub-paramter of a selected parent?
	 */
	isQueryParameterImportant(vars: Params, key: string) {
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
	typeToOperator(type?: string|null) {
		var operator = "";
		if (type === "regexp") {
			operator = "~";
		} else if (type === "notregexp") {
			operator = "!~";
		}
		return operator;
	}

}