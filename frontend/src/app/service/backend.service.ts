import { Injectable } from "@angular/core";
import { Params } from "@angular/router";
import { BehaviorSubject } from "rxjs";

import { SoftBreakSupportingDataSource } from '../component/result-table/result-table.component';
import { Commit } from "../model/commit";
import { ResultTransformator } from "../model/result.transformator";
import { mockdata } from './data';


@Injectable()
export class BackendService {

	getData(_params: Params) {
		let subject = new BehaviorSubject<SoftBreakSupportingDataSource<Commit> | undefined>(undefined);
		let t = new ResultTransformator(mockdata.config, mockdata.repositories);
		let dataSource = new SoftBreakSupportingDataSource(t.transform(mockdata.data));
		subject.next(dataSource);
		return subject;
	}

	getRepositoryList() {
		let subject = new BehaviorSubject<Record<string, Record<string, any>>|undefined>(undefined);
		subject.next(mockdata.repositories);
		return subject;
	}
}