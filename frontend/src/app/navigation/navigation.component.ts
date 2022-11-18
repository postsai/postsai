import { Component } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';

@Component({
  selector: 'app-navigation',
  templateUrl: './navigation.component.html'
})
export class NavigationComponent {
	public query?: Params;

	// TODO: Mobile navigation

	constructor(route: ActivatedRoute) {
		route.queryParams.subscribe((map) => {
			this.query = map;
		});
	}
}