from flask import Blueprint, render_template, redirect, url_for
from extensions import user_info_wrapper

tools_blueprint = Blueprint('tools', __name__)

@tools_blueprint.route('/')
def home():
	return redirect(url_for('tools.components'))

@tools_blueprint.route('/components/')
@user_info_wrapper
def components(username, role):
	return render_template('tools/components.html', username=username, role=role, active_page='components')

@tools_blueprint.route('/microgrids/', defaults={"id":None})
@tools_blueprint.route('/microgrids/<id>/')
@user_info_wrapper
def grids(username, role, id):
	if id is not None:
		return render_template('tools/grid/single.html', username=username, role=role, active_page='microgrids', id=id)
	return render_template('tools/grid/all.html', username=username, role=role, active_page='microgrids')

@tools_blueprint.route('/powerloads/', defaults={"id":None})
@tools_blueprint.route('/powerloads/<id>/')
@user_info_wrapper
def powerloads(username, role, id):
	if id is not None:
		return render_template('tools/powerload/single.html', username=username, role=role, active_page='powerloads', id=id)
	return render_template('tools/powerload/all.html', username=username, role=role, active_page='powerloads')
