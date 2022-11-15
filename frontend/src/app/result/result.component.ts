import { Component, HostListener } from '@angular/core';
import { mockdata } from './data';

@Component({
	selector: 'app-result',
	templateUrl: './result.component.html'
})
export class ResultComponent {
	public data = mockdata;

	public columnsToDisplay = ["repository", "when", "who", "file", "commit", "branch", "description"];
	
	breaks(value?: string) {
		if (!value) {
			return value;
		}
		return value.toString().replace(/([A-Z/_.@])/g, "\u200b$1");
	}

	formatTimestamp(value?: string) {
		if (!value) {
			return "-";
		}
		return value.substring(0, 16);
	}

	@HostListener('copy', ['$event'])
	onCopyHandler(event: ClipboardEvent) {
		let originalText = window.getSelection();
		if (originalText) {
			let text = originalText.toString().replace(/[\u200b-\u200d\ufeff]/g, '');
			event.clipboardData!.setData('text/plain', text);
			event.preventDefault();
		}
	}


}
