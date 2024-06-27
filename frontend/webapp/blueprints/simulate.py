from flask import Blueprint, render_template, redirect, url_for
from extensions import user_info_wrapper

simulate_blueprint = Blueprint('simulate', __name__)

@simulate_blueprint.route('/')
def home():
	return redirect(url_for('simulate.compute'))

@simulate_blueprint.route('/compute/')
@user_info_wrapper
def compute(username, role):
	return render_template(
		'tools/simulate/compute.html', 
		username=username, 
		role=role, 
		active_page='simulate', 
		active_sub_page='compute'
	)

@simulate_blueprint.route('/results/')
@user_info_wrapper
def results(username, role):
	return render_template(
			'tools/simulate/results.html', 
			username=username, 
			role=role, 
			active_page='simulate', 
			active_sub_page='results',
  		)
