import { Commit } from "./commit";
import { FileEntry } from "./fileentry";

export class ResultTransformator {

	constructor(
		private config: any,
		private repositories: any,
		) {
	}

	public transform(data: any[][]) {
		let res: Commit[] = [];
		for (let row of data) {
			res.push(this.transformRow(row));
		}
		return res;
	}

	public transformRow(entry: any[]): Commit {
		let commit = new Commit();
		commit.repository = entry[0];
		// commit.repositoryIcon
		commit.branch = entry[5];
		commit.when = entry[1];
		commit.who = entry[2];
		// commit.avatar
		commit.files = this.transformFileList(entry[3]);
		commit.commit = entry[9].substring(0, 8)
		commit.description = entry[7];
		return commit;
	}

	private transformFileList(list: string[]) {
		let res: FileEntry[] = [];
		for (let file of list) {
			res.push(new FileEntry(file, undefined));
		}
		return res;
	}
}