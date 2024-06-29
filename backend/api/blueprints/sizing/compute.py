from flask import Blueprint
from extensions import get_wrapper, run_analysis

sizing_compute_blueprint = Blueprint('sizing', __name__)

@sizing_compute_blueprint.route('/', methods=["POST"])
@get_wrapper(pass_user_id=True)
def sizing(user_id):
    return run_analysis(user_id, "sizing", time_limit= "2-00:00:00", send_email=True)
