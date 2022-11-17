import { Component, HostListener } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { ResultTransformator } from '../model/result.transformator';
import { mockdata } from './data';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public config: { [index:string] : any } = {};
	public repositories: { [index:string] : any } = {};
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
				this.dataSource = new MatTableDataSource(t.transform(response.data));
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
