import configparser
from flask import request, jsonify, current_app
from flask_mail import Mail
import jwt
import paramiko
from datetime import datetime
from functools import wraps
import traceback
import src.data.mysql.mysql_helpers as database_helpers
import src.data.mysql.users as database_users

CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")
SSH_KEY_FILENAME = CONFIG_INI.get("SSH","KEY_FILENAME",fallback=None)
SLURM_HOST = CONFIG_INI.get("SLURM","HOST",fallback=None)
SLURM_PORT = CONFIG_INI.get("SLURM","PORT",fallback=None)
SLURM_USERNAME = CONFIG_INI.get("SLURM","USERNAME",fallback=None)
SLURM_WORKING_DIRECTORY = CONFIG_INI.get("SLURM","WORKING_DIRECTORY",fallback=".")

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
    @wraps(f)
    def decorated(*args, **kwargs):
        encoded_token = None
        if "Authorization" in request.headers:
            bearer_token = request.headers["Authorization"]
            encoded_token = bearer_token.split()[1]
        if not encoded_token:
            return jsonify({'message' : 'API authentication token is missing'}), 401
        if encoded_token == "undefined":
            current_user = 2 # guest account
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
            except:
                return jsonify({'message' : 'API authentication token not registered to user.'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def get_wrapper(pass_user_id=False):
    def inner_decorator(f):
        @authorization_required
        def wrapper(user_id, *args, **kwargs):
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
    def inner_decorator(f):
        @authorization_required
        def wrapper(user_id, *args, **kwargs):
            try:
                request_dict = request.get_json()
                table_id = request_dict['id'] if 'id' in request_dict else None
                if database_users.has_permissions(user_id, table_id, table_name, action):
                    if pass_user_id and not pass_table_name:
                        data = f(request_dict, user_id, *args, **kwargs)
                    elif pass_user_id and pass_table_name:
                        data = f(request_dict, user_id, table_name, *args, **kwargs)
                    elif not pass_user_id and pass_table_name:
                        data = f(request_dict, table_name, *args, **kwargs)
                    else:
                        data = f(request_dict, *args, **kwargs)
                    request_dict['data'] = data
                    request_dict['processed'] = True
                    request_dict['status_message'] = "Success"
                else:
                    request_dict['processed'] = False
                    request_dict['status_message'] = "user not permitted to {0} {1} where id = {2}".format(
                        action, table_name, table_id
                    )
                request_dict['response_time'] = datetime.now()
            except Exception as error:
                raise APIException(f.__name__+"\n"+str(error), status_code=500)
            return jsonify(request_dict)
        wrapper.__name__ = f.__name__
        return wrapper
    return inner_decorator

def post_wrapper(table_name, action, pass_user_id=False, pass_table_name=False):
    def inner_decorator(f):
        @authorization_required
        def wrapper(user_id, *args, **kwargs):
            try:
                request_dict = request.get_json()
                table_id = request_dict['id'] if 'id' in request_dict else None
                if database_users.has_permissions(user_id, table_id, table_name, action):
                    if pass_user_id and not pass_table_name:
                        did_update, status_message = f(request_dict, user_id, *args, **kwargs)
                    elif pass_user_id and pass_table_name:
                        did_update, status_message = f(request_dict, user_id, table_name, *args, **kwargs)
                    elif not pass_user_id and pass_table_name:
                        did_update, status_message = f(request_dict, table_name, *args, **kwargs)
                    else:
                        did_update, status_message = f(request_dict, *args, **kwargs)                        
                    request_dict['processed'] = did_update
                    request_dict['status_message'] = status_message
                else:
                    request_dict['processed'] = False
                    request_dict['status_message'] = "user not permitted to {0} {1}".format(
                        action, table_name
                    )
                request_dict['response_time'] = datetime.now()
            except Exception as error:
                raise APIException(f.__name__+"\n"+str(error), status_code=500)
            return jsonify(request_dict)
        wrapper.__name__ = f.__name__
        return wrapper
    return inner_decorator

def update_name_description(request_dict, user_id, table_name):
    name = request_dict['name'] if 'name' in request_dict else None
    description = request_dict['description'] if 'description' in request_dict else None
    return database_helpers.update_name_description(
        user_id = user_id,
        table_name=table_name,
        id = request_dict['id'],
        name = name,
        description = description,
    )

def ssh_to_slurm(command):
    ssh_client = paramiko.SSHClient()
    try:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(username=SLURM_USERNAME, hostname=SLURM_HOST, port=SLURM_PORT, key_filename=SSH_KEY_FILENAME)
        stdin, stdout, stderr = ssh_client.exec_command("cd "+SLURM_WORKING_DIRECTORY+";"+command)
        print(stderr.read().decode('ascii').strip("\n"))
        if stdout.channel.recv_exit_status() != 0:
            raise Exception("SSH stderr: "+stderr.read().decode('ascii').strip("\n")+"\n"
                            +"SSH stdout: "+stdout.read().decode('ascii').strip("\n")+"\n")
    finally:
        ssh_client.close()
    return stdout.read().decode('ascii').strip("\n") if stdout else None
