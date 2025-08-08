import { Component } from '@angular/core';
import { NavigationComponent } from './component/navigation/navigation.component';
import { RouterOutlet } from '@angular/router';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    imports: [NavigationComponent, RouterOutlet]
})
export class AppComponent {
}
