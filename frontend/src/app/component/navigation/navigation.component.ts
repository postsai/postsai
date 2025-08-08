import { Component } from '@angular/core';
import { ActivatedRoute, Params, RouterLink } from '@angular/router';
import { MatToolbar } from '@angular/material/toolbar';
import { MatButton } from '@angular/material/button';

@Component({
    selector: 'app-navigation',
    templateUrl: './navigation.component.html',
    imports: [MatToolbar, MatButton, RouterLink]
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