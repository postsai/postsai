import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, ParamMap } from '@angular/router';

import { BackendService } from '../../service/backend.service';

import { Commit } from '../../model/commit';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public dataSource?: MatTableDataSource<Commit>;
	public queryParameters?: ParamMap;
	public search = '';

	constructor(route: ActivatedRoute, backendService: BackendService) {
		route.queryParamMap.subscribe((map) => {
			this.queryParameters = map;
			backendService.getData(map).subscribe((dataSource) => {
				this.dataSource = dataSource
			});
		});
	}

	applyFilter() {
		if (this.dataSource) {
			this.dataSource.filter = this.search.trim().toLowerCase();
		}
	}

}
