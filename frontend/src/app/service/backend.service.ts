import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Params, Router } from "@angular/router";


@Injectable()
export class BackendService {

	constructor(private http: HttpClient, private router: Router) {
	}

	getData(params: Params) {
		let url = this.router.createUrlTree([], { queryParams: params }).toString();
		let pos = url.indexOf('?');
		if (pos > -1) {
			url = url.substring(pos);
		} else {
			url = '';
		}
		return this.http.get('api.py' + url);
	}

	getRepositoryList() {
		return this.http.get('api.py?date=none');
	}

}