import os
import configparser
from flask import request, jsonify, current_app
from flask_mail import Mail, Message
import jwt
import paramiko
from datetime import datetime
from dateutil import parser
from functools import wraps
import traceback
import subprocess
import run.helpers as run_helpers
from src.data.mysql import mysql_microgrid
import src.data.mysql.users as database_users
from src.data.mysql import simulate, sizing

DATABASES = {"simulate": simulate, "sizing": sizing}

CONFIG_INI_GLOBAL = configparser.ConfigParser()
CONFIG_INI_GLOBAL.read(os.path.join(os.path.dirname(os.getcwd()),"config.ini"))
CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")
SSH_KEY_FILENAME = CONFIG_INI.get("SSH","KEY_FILENAME",fallback=None)
SLURM_HOST = CONFIG_INI.get("SLURM","HOST",fallback=None)
SLURM_PORT = CONFIG_INI.get("SLURM","PORT",fallback=None)
SLURM_USERNAME = CONFIG_INI.get("SLURM","USERNAME",fallback=None)
SLURM_WORKING_DIRECTORY = CONFIG_INI.get("SLURM","WORKING_DIRECTORY",fallback=".")
SLURM_RUN_LOCAL = CONFIG_INI.getboolean("SLURM","BYPASS_SLURM_RUN_LOCAL",fallback=False)
SLURM_FORCE_RECOMPUTE = CONFIG_INI.getboolean("SLURM","FORCE_RECOMPUTE",fallback=False)

mail = Mail()

class APIException(Exception):

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        self.traceback = traceback.format_exc()
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        response = dict(self.payload or ())
        response["message"] = self.message
        return response

def authorization_required(f):
    """Verifies that the API request has a valid token and is registered to a user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        encoded_token = None
        if "Authorization" in request.headers:
            bearer_token = request.headers["Authorization"]
            encoded_token = bearer_token.split()[1]
        if not encoded_token:
            return jsonify({'message' : 'API authentication token is missing'}), 401
        if encoded_token == "undefined":
            current_user = 2
            admin = False
        else:
            try:
                decoded_token = jwt.decode(encoded_token, current_app.secret_key, algorithms=["HS384"])
            except jwt.ExpiredSignatureError:
                return jsonify({'message' : 'API authentication token expired. Please log in again.'}), 401 
            except jwt.InvalidTokenError:
                return jsonify({'message' : 'API authentication token is not valid.'}), 401
            except:
                return jsonify({'message' : 'API authentication token decoding error.'}), 401
            try:
                current_user = decoded_token["sub"]
                admin = decoded_token["admin"]
            except:
                return jsonify({'message' : 'API authentication token not registered to user.'}), 401
        return f(current_user, admin, *args, **kwargs)
    return decorated

def get_wrapper(pass_user_id=False):
    """Handles get requests where API endpoint only requires user_id"""
    def inner_decorator(f):
        @authorization_required
        def wrapper(user_id, admin, *args, **kwargs):
            try:
                if pass_user_id:
                    data = f(user_id, *args, **kwargs)
                else:
                    data = f(*args, **kwargs)
                response_dict = {}
                response_dict['data'] = data
                response_dict['processed'] = True
                response_dict['status_message'] = "Success"
                response_dict['response_time'] = datetime.now()
            except Exception as error:
                raise APIException(f.__name__+"\n"+str(error), status_code=500)
            return jsonify(response_dict)
        wrapper.__name__ = f.__name__
        return wrapper
    return inner_decorator

def get_using_post_wrapper(table_name, action, pass_user_id=False, pass_table_name=False):
    """Handles post requests where API endpoint returns data but does not store any data to database"""
    def inner_decorator(f):
        @authorization_required
        def wrapper(user_id, admin, *args, **kwargs):
            response_dict = {}
            try:
                request_dict = request.get_json()
                table_id = request_dict['id'] if 'id' in request_dict else None
                if database_users.has_permissions(user_id, table_id, table_name, action, admin):
                    if pass_user_id and not pass_table_name:
                        data = f(request_dict, user_id, *args, **kwargs)
                    elif pass_user_id and pass_table_name:
                        data = f(request_dict, user_id, table_name, *args, **kwargs)
                    elif not pass_user_id and pass_table_name:
                        data = f(request_dict, table_name, *args, **kwargs)
                    else:
                        data = f(request_dict, *args, **kwargs)
                    response_dict['data'] = data
                    response_dict['processed'] = True
                    response_dict['status_message'] = "Success"
                else:
                    response_dict['processed'] = False
                    response_dict['status_message'] = "user not permitted to {0} {1} where id = {2}".format(
                        action, table_name, table_id
                    )
                response_dict['response_time'] = datetime.now()
            except Exception as error:
                raise APIException(f.__name__+"\n"+str(error), status_code=500)
            return jsonify(response_dict)
        wrapper.__name__ = f.__name__
        return wrapper
    return inner_decorator

def post_wrapper(table_name, action, pass_user_id=False, pass_table_name=False):
    """Handles post requests where API endpoint does not return any data"""
    def inner_decorator(f):
        @authorization_required
        def wrapper(user_id, admin, *args, **kwargs):
            response_dict = {}
            try:
                request_dict = request.get_json()
                table_id = request_dict['id'] if 'id' in request_dict else None
                if database_users.has_permissions(user_id, table_id, table_name, action, admin):
                    if pass_user_id and not pass_table_name:
                        did_update, status_message = f(request_dict, user_id, *args, **kwargs)
                    elif pass_user_id and pass_table_name:
                        did_update, status_message = f(request_dict, user_id, table_name, *args, **kwargs)
                    elif not pass_user_id and pass_table_name:
                        did_update, status_message = f(request_dict, table_name, *args, **kwargs)
                    else:
                        did_update, status_message = f(request_dict, *args, **kwargs)                      
                    response_dict['processed'] = did_update
                    response_dict['status_message'] = status_message
                else:
                    response_dict['processed'] = False
                    response_dict['status_message'] = "user not permitted to {0} {1}".format(
                        action, table_name
                    )
                response_dict['response_time'] = datetime.now()
            except Exception as error:
                raise APIException(f.__name__+"\n"+str(error), status_code=500)
            return jsonify(response_dict)
        wrapper.__name__ = f.__name__
        return wrapper
    return inner_decorator

def post_then_get_wrapper(table_name, action, pass_user_id=False, pass_table_name=False):
    """Handles post requests where API endpoint both accepts data to process and returns data after processing"""
    def inner_decorator(f):
        @authorization_required
        def wrapper(user_id, admin, *args, **kwargs):
            response_dict = {}
            try:
                request_dict = request.get_json()
                table_id = request_dict['id'] if 'id' in request_dict else None
                if database_users.has_permissions(user_id, table_id, table_name, action, admin):
                    if pass_user_id and not pass_table_name:
                        did_update, status_message, data = f(request_dict, user_id, *args, **kwargs)
                    elif pass_user_id and pass_table_name:
                        did_update, status_message, data = f(request_dict, user_id, table_name, *args, **kwargs)
                    elif not pass_user_id and pass_table_name:
                        did_update, status_message, data = f(request_dict, table_name, *args, **kwargs)
                    else:
                        did_update, status_message, data = f(request_dict, *args, **kwargs)
                    response_dict['data'] = data
                    response_dict['processed'] = did_update
                    response_dict['status_message'] = status_message
                else:
                    response_dict['processed'] = False
                    response_dict['status_message'] = "user not permitted to {0} {1}".format(
                        action, table_name
                    )
                response_dict['response_time'] = datetime.now()
            except Exception as error:
                raise APIException(f.__name__+"\n"+str(error), status_code=500)
            return jsonify(response_dict)
        wrapper.__name__ = f.__name__
        return wrapper
    return inner_decorator

def update_name_description(request_dict, user_id, table_name):
    """Updates the name and description of a table entry."""
    name = request_dict['name'] if 'name' in request_dict else None
    description = request_dict['description'] if 'description' in request_dict else None
    return mysql_microgrid.update_name_description(
        user_id = user_id,
        table_name=table_name,
        id = request_dict['id'],
        name = name,
        description = description,
    )

def result_add_to_database(user_id, table_name):
    """Adds a result to the database if it does not already exist."""
    request_dict = request.get_json()
    try:
        startdatetime = parser.parse(request_dict[run_helpers.STARTDATETIME])
    except Exception as error:
        raise ValueError("startdatetime not valid:\n"+str(error))
    try:
        enddatetime = parser.parse(request_dict[run_helpers.ENDDATETIME])
    except Exception as error:
        raise ValueError("enddatetime not valid:\n"+str(error))
    location_id = request_dict[run_helpers.LOCATION_ID]
    load_id = request_dict[run_helpers.LOAD_ID]
    grid_id = request_dict[run_helpers.GRID_ID]
    energy_management_system_id = request_dict[run_helpers.ENERGY_MANAGEMENT_SYSTEM_ID]
    try:
        if not database_users.has_permissions(user_id, grid_id, "grid", "read"):
            raise ValueError("User does not have permission to access grid")
        if not database_users.has_permissions(user_id, load_id, "powerload", "read"):
            raise ValueError("User does not have permission to access load")
    except Exception as error:
        raise RuntimeError("Error in blueprint checking user permissions\n"+str(error))
    id = DATABASES[table_name].MODEL_HELPERS.result_get_by_params(
        grid_id=grid_id,
        energy_management_system_id=energy_management_system_id,
        powerload_id=load_id,
        location_id=location_id,
        startdatetime=startdatetime,
        enddatetime=enddatetime,
    )
    if SLURM_FORCE_RECOMPUTE:
        DATABASES[table_name].MODEL_HELPERS.remove(id)
        id = None
    if id is not None: return True, id
    return False, DATABASES[table_name].MODEL_HELPERS.result_add(
            user_id=user_id,
            grid_id=grid_id,
            energy_management_system_id=energy_management_system_id,
            powerload_id=load_id,
            location_id=location_id,
            startdatetime=startdatetime,
            enddatetime=enddatetime,
        )

def ssh_to_slurm(command):
    """Connects to the SLURM server and runs the input command."""
    ssh_client = paramiko.SSHClient()
    try:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(username=SLURM_USERNAME, hostname=SLURM_HOST, port=SLURM_PORT, key_filename=SSH_KEY_FILENAME)
        stdin, stdout, stderr = ssh_client.exec_command("cd "+SLURM_WORKING_DIRECTORY+";"+command)
        if stdout.channel.recv_exit_status() != 0:
            raise Exception("SSH stdin: "+stdin.read().decode('ascii').strip("\n")+"\n"
                            +"SSH stderr: "+stderr.read().decode('ascii').strip("\n")+"\n"
                            +"SSH stdout: "+stdout.read().decode('ascii').strip("\n")+"\n")
    finally:
        ssh_client.close()
    return stdout.read().decode('ascii').strip("\n") if stdout else None

def compute(user_id, table_name, compute_id, time_limit, script=None, send_email=False):
    """Submits a job to the SLURM server to run the analysis or runs it locally."""
    if script is None: script = "run/compute.py"
    if not database_users.has_permissions(user_id, compute_id, table_name, "write"):
        raise ValueError("User does not have permission to access {0} result".format(table_name))
    try:
        if SLURM_RUN_LOCAL:
            subprocess.Popen(["python", script, "-m", table_name, "-r", str(compute_id)])
            job_response =  "Submitted batch job 0"
        else:
            job_response = ssh_to_slurm("run/compute_sbatch_wrapper.sh {0} {1} {2} {3}".format(
                table_name, compute_id, time_limit, script
            ))
    except Exception as error:
        raise RuntimeError("Error in {0} blueprint running analysis\n{1}".format(table_name, error))
    if job_response and job_response.startswith("Submitted batch job "): 
        job_response = job_response.split("Submitted batch job ")[1]
    if job_response is None or not job_response.isdigit():
        DATABASES[table_name].MODEL_HELPERS.remove(compute_id)
        raise RuntimeError("Compute job failed to execute. Please try again.")
    if send_email and not CONFIG_INI_GLOBAL.getboolean("MAIL","MAIL_DISABLE_FOR_RUN_LOCAL",fallback=False):
        email = database_users.email_get(user_id)
        email_info = Message("{0} analysis in progress: id = {1}".format(table_name, compute_id), 
                                sender = current_app.config['MAIL_USERNAME'], recipients = [email], 
                                reply_to = current_app.config['MAIL_REPLY_TO'])
        email_info.body = "You will receive another email when your job completes. " \
                        + "The result id is {0} and the Slurm ID is {1}.".format(compute_id, job_response)
        mail.send(email_info)
    return job_response

def run_analysis(user_id, table_name, time_limit="2-00:00:00", script=None, send_email=False):
    """Run an analysis."""
    try:
        exists_flag, id = result_add_to_database(user_id, table_name)
        if not exists_flag or SLURM_FORCE_RECOMPUTE:
            compute_job_id = compute(user_id, table_name, id, time_limit, script, send_email)
            DATABASES[table_name].MODEL_HELPERS.compute_job_info_add(id, compute_job_id)
        else:
            compute_job_id = None
    except Exception as error:
        raise RuntimeError("Error in running {0} analysis\n{1}".format(table_name, error))
    return { "compute_id": id, "compute_job_id": compute_job_id }
