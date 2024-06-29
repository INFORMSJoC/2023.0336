from flask import Blueprint, request
from flask import current_app as app
from flask_mail import Message
from extensions import mail
from dateutil import parser
from extensions import get_wrapper, post_wrapper, ssh_to_slurm
import run.helpers as run_helpers
import src.data.mysql.sizing as database_sizing
import src.data.mysql.users as database_users

def sizing_run_add_to_database(user_id):
    request_dict = request.get_json()
    try:
        date_time = parser.parse(request_dict[run_helpers.STARTDATETIME])
    except Exception as error:
        raise ValueError("startdatetime not valid:\n"+str(error))
    load_id = request_dict[run_helpers.LOAD_ID]
    grid_id = request_dict[run_helpers.GRID_ID]
    try:
        if not database_users.has_permissions(user_id, grid_id, "grid", "read"):
            raise ValueError("User does not have permission to access grid")
        if not database_users.has_permissions(user_id, load_id, "powerload", "read"):
            raise ValueError("User does not have permission to access load")
    except Exception as error:
        raise RuntimeError("Error in sizing blueprint checking user permissions\n"+str(error))
    return database_sizing.run_add(
            user_id=user_id,
            grid_id=grid_id,
            powerload_id=load_id,
            startdatetime=date_time,
        )

def compute(user_id, run_id):
    if not database_users.has_permissions(user_id, run_id, "sizing", "write"):
        raise ValueError("User does not have permission to access sizing run")
    run_info = database_sizing.run_get(run_id)
    try:
        response = ssh_to_slurm("qsub run/sizing/sizing.sbatch -r "+str(run_id))
        return response
    except Exception as error:
        database_sizing.remove(run_id)
        raise RuntimeError("Error in sizing blueprint running analysis\n"+str(error))


sizing_compute_blueprint = Blueprint('sizing', __name__)

@sizing_compute_blueprint.route('/add/', methods=["POST"])
@get_wrapper(pass_user_id=True)
def run_add(user_id):
    return sizing_run_add_to_database(user_id)

@sizing_compute_blueprint.route('/run/', methods=["POST"])
@get_wrapper(pass_user_id=True)
def sizing_run(user_id):
    run_id = request.get_json()['id']
    email = database_users.email_get(user_id)
    try:
        slurm_id = compute(user_id, run_id)
        email_info = Message('Sizing analysis in progress: id = '+str(run_id), sender = app.config['MAIL_USERNAME'], recipients = [email])
        email_info.body = "You will receive another email when your job completes. " \
                           + "The run id is {0} and the Slurm ID is {1}.".format(run_id, slurm_id)
        mail.send(email_info)
    except Exception as error:
        raise RuntimeError("Error in sizing DOE blueprint running DOE\n"+str(error))
    return slurm_id
