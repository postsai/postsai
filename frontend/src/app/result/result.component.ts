import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, ParamMap } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { ResultTransformator } from '../model/result.transformator';
import { SoftBreakSupportingDataSource } from '../result-table/result-table.component';
import { mockdata } from './data';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public dataSource = new MatTableDataSource<any>([]);
	public queryParameters?: ParamMap;
	public search = '';

	constructor(route: ActivatedRoute) {
		route.queryParamMap.subscribe((map) => {
			this.queryParameters = map;
			new BehaviorSubject(mockdata).subscribe((response) => {
				let t = new ResultTransformator(response.config, response.repositories);
				this.dataSource = new SoftBreakSupportingDataSource(t.transform(response.data));
			});
		});
	}

	applyFilter() {
		this.dataSource.filter = this.search.trim().toLowerCase();
	}

}
