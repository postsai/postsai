import * as tsmd5 from 'ts-md5';

import { Commit } from "./commit";
import { FileEntry } from "./fileentry";


export class ResultTransformator {
	private hashCache: Record<string, string> = {};

	constructor(
		private config: any,
		private repositories: any,
	) {
	}

	private getRepoProp(repository: string, key: string, fallback?: any) {
		if (!this.repositories) {
			return fallback;
		}
		let repoConfig = this.repositories[repository];
		if (!repoConfig) {
			return fallback;
		}
		return (repoConfig[key] !== "") ? repoConfig[key] : fallback;
	}

	private guessSCM(revision: string) {
		if ((revision === "") || revision.indexOf(".") >= 0) {
			return "cvs";
		} else if (revision.length < 40) {
			return "subversion";
		}
		return "git";
	}

	private entryToProp(entry: any[]) {
		let scm = this.guessSCM(entry[4][0]);
		let commit = entry[9];
		if (!commit) {
			commit = entry[4][0];
		}
		let prop = {
			"repository": entry[0].replace("/srv/cvs/", "").replace("/var/lib/cvs/"),
			"file": entry[3],
			"revision": entry[4],
			"commit": commit,
			"short_commit": commit,
			"scm": scm
		};
		if (scm === "cvs") {
			prop["short_commit"] = commit.substring(commit.length - 8, commit.length);
		}
		if (scm === "git") {
			prop["short_commit"] = commit.substring(0, 8);
		}
		return prop;
	}

	argsubst(str: string, prop: Record<string, string>) {
		if (!str) {
			return str;
		}
		let posOpen = str.indexOf('[');
		let posClose = -1;
		if (posOpen < 0) {
			return str;
		}
		let res = '';
		while (posOpen > - 1) {
			res = res + str.substring(posClose + 1, posOpen);
			posClose = str.indexOf(']', posOpen);
			if (posClose < 0) {
				return res + str.substring(posOpen);
			}
			let key = str.substring(posOpen + 1, posClose);
			res = res + prop[key];
			posOpen = str.indexOf('[', posClose);
		}
		res = res + str.substring(posClose + 1);
		return res;
	}

	hashWithCache(input: string) {
		let hash = this.hashCache[input];
		if (!hash) {
			const md5 = new tsmd5.Md5();
			hash = md5.appendStr(input).end() as string;
			this.hashCache[input] = hash;
		}
		return hash;
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
		let prop = this.entryToProp(entry);
		commit.repository = entry[0];
		commit.repositoryIcon = this.transformRepositoryIcon(prop, commit.repository);
		commit.branch = entry[5];
		commit.when = entry[1].substring(0, 16);
		commit.who = this.transformAuthor(entry[2]);
		commit.avatar = this.transformAvatar(entry[2]);
		commit.files = this.transformFileList(prop, commit.repository, entry[3], entry[4]);
		commit.commit = entry[9].substring(0, 8)
		commit.commitUrl = this.transformDiffLink(prop, commit.repository, entry[9]);
		commit.description = this.formatDescription(commit.repository, entry[7]);
		return commit;
	}

	private transformRepositoryIcon(prop: Record<string, string>, repository: string) {
		let iconUrl = this.getRepoProp(repository, "icon_url", this.config.icon_url);
		return this.argsubst(iconUrl, prop);
	}

	private transformAuthor(mail: string) {
		if (this.config.trim_email) {
			return mail.replace(/@.*/, "");
		}
		return mail;
	}

	private transformAvatar(mail: string) {
		if (!this.config.avatar) {
			return undefined;
		}
		return this.config.avatar + "/avatar/" + this.hashWithCache(mail) + ".jpg?s=20&d=wavatar";
	}

	private transformFileList(prop: Record<string, string>, repository: string, list: string[], revisions: string[]) {
		let url = this.getRepoProp(repository, "file_url");
		let res: FileEntry[] = [];
		for (var i = 0; i < list.length; i++) {
			let file = list[i];
			prop['file'] = file;
			prop['revision'] = revisions[i];
			res.push(new FileEntry(file, this.argsubst(url, prop)));
		}
		return res;
	}

	private transformDiffLink(prop: Record<string, string>, repository: string, revision: string) {
		if (!revision) {
			return undefined;
		}
		let url = this.getRepoProp(repository, "commit_url");
		return this.argsubst(url, prop);
	}

	/**
	 * formats the description column to link to an issue tracker
	 */
	private formatDescription(repository: string, description?: string) {
		if (!description) {
			return "-";
		}
		let url = this.getRepoProp(repository, "tracker_url", this.config.tracker);

		// HTML escpale 
		let e = document.createElement("div");
		e.innerText = description.replace(/([A-Z/_.@])/g, "\u200b$1");
		let text = e.innerHTML;
		if (!url) {
			return text;
		}
		return text.replace(/#([0-9]+)/g, '<a href="' + url + '">#$1</a>');
	}

}
