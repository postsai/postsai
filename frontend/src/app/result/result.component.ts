import { Component, HostListener } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { ResultTransformator } from '../model/result.transformator';
import { mockdata } from './data';


class DataSource<T> extends MatTableDataSource<T> {

	override filterPredicate: (data: T, filter: string) => boolean = (data: T, filter: string): boolean => {
		const matchSoftBreakCharacters = /[\u200b-\u200d\ufeff\u00ad]/g

		// Transform the data into a lowercase string of all property values.
		const dataStr = Object.keys(data as unknown as Record<string, any>)
			.reduce((currentTerm: string, key: string) => {
				// Use an obscure Unicode character to delimit the words in the concatenated string.
				// This avoids matches where the values of two columns combined will match the user's query
				// (e.g. `Flute` and `Stop` will match `Test`). The character is intended to be something
				// that has a very low chance of being typed in by somebody in a text field. This one in
				// particular is "White up-pointing triangle with dot" from
				// https://en.wikipedia.org/wiki/List_of_Unicode_characters
				let cellValue = (data as unknown as Record<string, any>)[key] || '';
				return currentTerm + cellValue.toString().replace(matchSoftBreakCharacters, '') + '◬';
			}, '')
			.toLowerCase();

		// Transform the filter by converting it to lowercase and removing whitespace.
		const transformedFilter = filter.trim().toLowerCase().replace(matchSoftBreakCharacters, '');

		return dataStr.indexOf(transformedFilter) != -1;
	};
}


@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public config: { [index: string]: any } = {};
	public repositories: { [index: string]: any } = {};
	public dataSource = new MatTableDataSource<any>([]);
	public columnsToDisplay = ["repository", "when", "who", "file", "commit", "branch", "description"];
	public queryParameters?: ParamMap;
	public search = '';

	constructor(route: ActivatedRoute) {
		route.queryParamMap.subscribe((map) => {
			this.queryParameters = map;
			new BehaviorSubject(mockdata).subscribe((response) => {
				this.config = response.config;
				this.repositories = response.repositories;
				let t = new ResultTransformator(response.config, response.repositories);
				this.dataSource = new DataSource(t.transform(response.data));
			});
		});
	}

	applyFilter() {
		this.dataSource.filter = this.search.trim().toLowerCase();
	}

	breaks(value?: string) {
		if (!value) {
			return value;
		}
		return value.toString().replace(/([A-Z/_.@])/g, "\u200b$1");
	}

	forceBreakAfter(value: string|undefined, char: string) {
		if (!value) {
			return value;
		}
		let pos = value.lastIndexOf(char);
		if (pos > -1) {
			return value.substring(0, pos + 1) + "\n" + value.substring(pos + 1);
		}
		return value;
	}

	forceBreakBefore(value: string|undefined, char: string) {
		if (!value) {
			return value;
		}
		let pos = value.lastIndexOf(char);
		if (pos > -1) {
			return value.substring(0, pos) + "\n" + value.substring(pos);
		}
		return value;
	}

	@HostListener('copy', ['$event'])
	onCopyHandler(event: ClipboardEvent) {
		let originalText = window.getSelection();
		if (originalText) {
			let text = originalText.toString().replace(/[\u200b-\u200d\ufeff]/g, '');
			event.clipboardData!.setData('text/plain', text);
			event.preventDefault();
		}
	}

}
