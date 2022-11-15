import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ResultComponent } from './result/result.component';

const routes: Routes = [
	{
		path: 'query.html',
		component: ResultComponent
	},
	{
		path: '',
		pathMatch: 'prefix',
		redirectTo: 'query.html'
	}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
