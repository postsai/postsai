import { Component } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { BackendService } from '../../service/backend.service';

import { Commit } from '../../model/commit';
import { ResultTransformator } from 'src/app/model/result.transformator';
import { SoftBreakSupportingDataSource } from '../result-table/result-table.component';
import { MatCheckboxChange } from '@angular/material/checkbox';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public error: any;
	public config: Record<string, any> = {};
	public dataSource?: MatTableDataSource<Commit>;
	public queryParameters?: Params;
	public search = '';
	public includeForks = false;

	constructor(route: ActivatedRoute, private router: Router, backendService: BackendService) {
		route.queryParams.subscribe((map) => {
			this.queryParameters = JSON.parse(JSON.stringify(map));
			if (!map['forked_from'] && map['forked_from'] !== '') {
				this.queryParameters!['forked_from'] = '-';
			}
			this.includeForks = this.queryParameters!['forked_from'] !== '-';
			backendService.getData(this.queryParameters!).subscribe({
				next: (data: any) => {
					let t = new ResultTransformator(data.config, data.repositories);
					this.dataSource = new SoftBreakSupportingDataSource(t.transform(data.data));
					this.config = data.config;
				},
				error: (error: any) => {
					this.error = error;
				}
			});
		});
	}

	onIncludeForksChange() {
		if (!this.queryParameters) {
			return;
		}
		if (this.includeForks) {
			this.queryParameters["forked_from"] = "";
		} else {
			this.queryParameters["forked_from"] = "-";
		}
		this.router.navigate(['/query.html'], { queryParams: this.queryParameters });
	}

	applyFilter() {
		if (this.dataSource) {
			this.dataSource.filter = this.search.trim().toLowerCase();
		}
	}

}
