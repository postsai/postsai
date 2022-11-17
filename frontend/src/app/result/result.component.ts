import { Component, HostListener } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { mockdata } from './data';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public data = mockdata;
	public dataSource = new MatTableDataSource<any>([]);
	public columnsToDisplay = ["repository", "when", "who", "file", "commit", "branch", "description"];
	public queryParameters?: ParamMap;
	public search = '';

	constructor(route: ActivatedRoute) {
		route.queryParamMap.subscribe((map) => {
			this.queryParameters = map;
			this.dataSource = new MatTableDataSource(this.data.data);
		})
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

	formatTimestamp(value?: string) {
		if (!value) {
			return "-";
		}
		return value.substring(0, 16);
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
