import { Component } from '@angular/core';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public data = {
		"additional_scripts": [],
		"config": {
			"service_worker": false,
			"trim_email": false
		},
		"data": [
			[
				"a/repository",
				"2022-11-15 15:17:15",
				"someone@example.com",
				[
					"foo/bar/i18n_en.txt"
				],
				[
					"dbcab2425803a31f5f15af28f6a31ddbfc02608e"
				],
				"RELEASE_2022_12",
				"0/0",
				"removed old i18n-key #290392\n",
				"a/repository",
				"dbcab2425803a31f5f15af28f6a31ddbfc02608e",
				""
			],
			[
				"a/repository",
				"2022-11-15 15:14:39",
				"somebody@example.com",
				[
					"src/test/Test"
				],
				[
					"f5aab4565b592ef32306c5449fa247a09ed2abc5"
				],
				"",
				"0/0",
				"#290216 Abnahme Testfall 19870",
				"a/repository",
				"f5aab4565b592ef32306c5449fa247a09ed2abc5",
				""
			]
		]
	};
	public columnsToDisplay = ["repository", "when", "who", "file", "commit", "branch", "description"];
}
