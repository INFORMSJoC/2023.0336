from flask import Blueprint, render_template, redirect, url_for
from extensions import user_info_wrapper

resilience_blueprint = Blueprint('resilience', __name__)

@resilience_blueprint.route('/')
def home():
	return redirect(url_for('resilience.run'))

@resilience_blueprint.route('/disturbances/')
@user_info_wrapper
def disturbances(username, role):
	return render_template(
		'tools/resilience/disturbances.html',
		username=username,
		role=role,
		active_page='resilience',
		active_sub_page='disturbances'
	)

@resilience_blueprint.route('/repairs/')
@user_info_wrapper
def repairs(username, role):
	return render_template(
		'tools/resilience/repairs.html',
		username=username,
		role=role,
		active_page='resilience',
		active_sub_page='repairs'
	)

@resilience_blueprint.route('/run/')
@user_info_wrapper
def run(username, role):
	return render_template(
		'tools/resilience/run.html',
		username=username,
		role=role,
		active_page='resilience',
		active_sub_page='run'
	)
