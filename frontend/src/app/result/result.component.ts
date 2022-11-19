import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { BehaviorSubject, delay } from 'rxjs';
import { Commit } from '../model/commit';
import { ResultTransformator } from '../model/result.transformator';
import { SoftBreakSupportingDataSource } from '../result-table/result-table.component';
import { mockdata } from './data';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public dataSource?: MatTableDataSource<Commit>;
	public queryParameters?: ParamMap;
	public search = '';

	constructor(route: ActivatedRoute) {
		route.queryParamMap.subscribe((map) => {
			this.queryParameters = map;
			new BehaviorSubject(mockdata).pipe(delay(1)).subscribe((response) => {
				let t = new ResultTransformator(response.config, response.repositories);
				this.dataSource = new SoftBreakSupportingDataSource(t.transform(response.data));
			});
		});
	}

	applyFilter() {
		if (this.dataSource) {
			this.dataSource.filter = this.search.trim().toLowerCase();
		}
	}

}
