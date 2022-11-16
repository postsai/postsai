import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { LayoutModule } from '@angular/cdk/layout';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';

import { NavigationComponent } from './navigation/navigation.component';
import { ResultComponent } from './result/result.component';
import { MatTableResponsiveDirective } from './mat-table-responsive/mat-table-responsive.directive';
import { QueryParameterPipe } from './queryparameter/queryparameter.pipe';

@NgModule({
	declarations: [
		MatTableResponsiveDirective,

		AppComponent,
		NavigationComponent,
		QueryParameterPipe,
		ResultComponent
	],
	imports: [
		BrowserModule,
		AppRoutingModule,
		BrowserAnimationsModule,
		LayoutModule,
		MatButtonModule,
		MatListModule,
		MatIconModule,
		MatTableModule,
		MatToolbarModule
	],
	providers: [],
	bootstrap: [AppComponent]
})
export class AppModule { }
