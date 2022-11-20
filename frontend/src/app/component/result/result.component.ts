import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, Params } from '@angular/router';

import { BackendService } from '../../service/backend.service';

import { Commit } from '../../model/commit';
import { ResultTransformator } from 'src/app/model/result.transformator';
import { SoftBreakSupportingDataSource } from '../result-table/result-table.component';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public dataSource?: MatTableDataSource<Commit>;
	public queryParameters?: Params;
	public search = '';

	constructor(route: ActivatedRoute, backendService: BackendService) {
		route.queryParams.subscribe((map) => {
			this.queryParameters = map;
			backendService.getData(map).subscribe((data: any) => {
				let t = new ResultTransformator(data.config, data.repositories);
				this.dataSource = new SoftBreakSupportingDataSource(t.transform(data.data));
			});
		});
	}

	applyFilter() {
		if (this.dataSource) {
			this.dataSource.filter = this.search.trim().toLowerCase();
		}
	}

}
