from flask import Blueprint, render_template
from extensions import user_info_wrapper, clear_session_data

toplevel_blueprint = Blueprint('toplevel', __name__)

@toplevel_blueprint.route('/')
@user_info_wrapper
def home(username, role):
	return render_template('index.html', username=username, role=role)

@toplevel_blueprint.route('/clear_session/')
def clear_session():
	return clear_session_data(login_redirect=True)
