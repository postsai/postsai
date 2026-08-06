import { Component, signal } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { BackendService } from 'src/app/service/backend.service';
import { FormsModule } from '@angular/forms';
import { MatRadioGroup, MatRadioButton } from '@angular/material/radio';
import { MatAutocompleteTrigger, MatAutocomplete, MatOption } from '@angular/material/autocomplete';
import { MatButton } from '@angular/material/button';

@Component({
    selector: 'app-search',
    templateUrl: './search.component.html',
    imports: [FormsModule, MatRadioGroup, MatRadioButton, MatAutocompleteTrigger, MatAutocomplete, MatOption, MatButton]
})
export class SearchComponent {
	
	public params: Record<string, string> = {};
	public repositories?: string[];
	public filteredRepositories = signal<string[]>([]);

	constructor(
		backendService: BackendService,
		private router: Router,
		route: ActivatedRoute
	) {
		route.queryParams.subscribe((map) => {
			let params = JSON.parse(JSON.stringify(map));
			params['descriptiontype'] = params['descriptiontype'] || 'search';
			params['repository'] = params['repository'] || '';
			params['repositorytype'] = params['repositorytype'] || 'match';
			params['branchtype'] = params['branchtype'] || 'match';
			params['dirtype'] = params['dirtype'] || 'match';
			params['filetype'] = params['filetype'] || 'match';
			params['whotype'] = params['whotype'] || 'match';
			params['committype'] = params['committype'] || 'match';
			params['date'] = params['date'] || 'day';
			this.params = params;
		});
		backendService.getRepositoryList().subscribe((data: any) => {
			this.repositories = Object.keys(data.repositories);
		});

	}

	onRepositoryChange() {
		let filter = this.params['repository'].toLowerCase();
		this.filteredRepositories.set(this.repositories!.filter((value) => {
			return value.toLowerCase().indexOf(filter) > -1;
		}))
	}

	onSearch(_event: any) {
		this.router.navigate(['/query.html'], { queryParams: this.params });
	}
}
