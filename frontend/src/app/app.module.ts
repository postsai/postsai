import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { LayoutModule } from '@angular/cdk/layout';
import { RouterModule } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatGridListModule } from '@angular/material/grid-list'; 
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule} from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatRadioModule } from '@angular/material/radio';
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTableResponsiveDirective } from './mat-table-responsive/mat-table-responsive.directive';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { NavigationComponent } from './navigation/navigation.component';
import { ResultComponent } from './result/result.component';
import { QueryParameterPipe } from './queryparameter/queryparameter.pipe';
import { SearchComponent } from './search/search.component';

@NgModule({
	declarations: [
		MatTableResponsiveDirective,

		AppComponent,
		NavigationComponent,
		QueryParameterPipe,
		SearchComponent,
		ResultComponent
	],
	imports: [
		BrowserModule,
		AppRoutingModule,
		BrowserAnimationsModule,
		FormsModule,
		LayoutModule,
		MatButtonModule,
		MatGridListModule,
		MatIconModule,
		MatInputModule,
		MatListModule,
		MatRadioModule,
		MatTableModule,
		MatToolbarModule,
		RouterModule
	],
	providers: [],
	bootstrap: [AppComponent]
})
export class AppModule { }
