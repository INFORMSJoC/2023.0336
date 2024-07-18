from flask import Blueprint
from extensions import get_wrapper, run_analysis

simulate_compute_blueprint = Blueprint('simulate', __name__)

@simulate_compute_blueprint.route('/', methods=["POST"])
@get_wrapper(pass_user_id=True)
def simulate(user_id):
    return run_analysis(user_id, "simulate", time_limit= "0-01:00:00", send_email=False)
