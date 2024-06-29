from flask import Blueprint, render_template, redirect, url_for
from extensions import user_info_wrapper

sizing_blueprint = Blueprint('sizing', __name__)

@sizing_blueprint.route('/')
def home():
	return redirect(url_for('sizing.results'))

@sizing_blueprint.route('/microgrids/', defaults={"id":None})
@sizing_blueprint.route('/microgrids/<id>/')
@user_info_wrapper
def grids(username, role, id):
	if id is not None:
		return render_template(
			'tools/sizing/grid.html', 
			username=username, 
			role=role, 
			active_page='sizing',
			active_sub_page='grids',
			id=id,
		)
	return render_template(
		'tools/sizing/grids.html',
		username=username, 
		role=role, 
		active_page='sizing',
		active_sub_page='grids'
  	)

@sizing_blueprint.route('/run/')
@user_info_wrapper
def run(username, role):
	return render_template(
		'tools/sizing/run.html', 
		username=username, 
		role=role, 
		active_page='sizing', 
		active_sub_page='run'
	)

@sizing_blueprint.route('/results/', defaults={"id":None})
@sizing_blueprint.route('/results/<id>/')
@user_info_wrapper
def results(username, role, id):
	if id is not None:
		return render_template(
				'tools/sizing/result.html', 
				username=username, 
				role=role, 
				active_page='sizing', 
				active_sub_page='results',
				id=id,
			)
	return render_template(
			'tools/sizing/results.html', 
			username=username, 
			role=role, 
			active_page='sizing', 
			active_sub_page='results',
  		)
