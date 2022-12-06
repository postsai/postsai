import { FileEntry } from "./fileentry";

export class Commit {
	public repository!: string;
	public repositoryIcon?: string;
	public branch?: string;
	public when!: string;
	public who!: string
	public avatar?: string;
	public files!: FileEntry[];
	public commit!: string;
	public commitUrl?: string;
	public description!: string;

}