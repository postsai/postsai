import { Component, ChangeDetectionStrategy } from '@angular/core';
import { NavigationComponent } from './component/navigation/navigation.component';
import { RouterOutlet } from '@angular/router';

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    imports: [NavigationComponent, RouterOutlet]
})
export class AppComponent {
}
