import { Component } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html'
})
export class SearchComponent {
	public params: Record<string, string> = {};

	constructor(private router: Router, route: ActivatedRoute) {
		route.queryParams.subscribe((map) => {
			let params = JSON.parse(JSON.stringify(map));
			params['descriptiontype'] = params['descriptiontype'] || 'search';
			params['repositorytype'] = params['repositorytype'] || 'match';
			params['branchtype'] = params['branchtype'] || 'match';
			params['dirtype'] = params['dirtype'] || 'match';
			params['filetype'] = params['filetype'] || 'match';
			params['whotype'] = params['whotype'] || 'match';
			params['committype'] = params['committype'] || 'match';
			params['date'] = params['date'] || 'day';
			this.params = params;
		});
	}

	onSearch(_event: any) {
		this.router.navigate(['/query.html'], { queryParams: this.params });
	}
}
