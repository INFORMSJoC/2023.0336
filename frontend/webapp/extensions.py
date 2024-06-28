from flask import session, make_response, request, redirect, url_for
from flask_mail import Mail
from flask_mysqldb import MySQL
from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
import hashlib
import configparser

CONFIG_INI = configparser.ConfigParser()
CONFIG_INI.read("config.ini")

mail = Mail()
mysql = MySQL()

def user_info_wrapper(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if is_session_active():
            username=display_user(session['username'])
            role=session['role']
        else:
            username="guest"
            role="Guest"
        return f(username, role, *args, **kwargs)
    return decorated

def is_session_active():
	if "id" not in session:
		return False
	return True

def json_web_token(user_id, secret_key, admin=False):
    """Generates a JSON web token for API authorization"""
    try:
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(
                days=CONFIG_INI.getint("JWT","EXPIRES_DAYS"),
                hours=CONFIG_INI.getint("JWT","EXPIRES_HOURS"),
                minutes=CONFIG_INI.getint("JWT","EXPIRES_MINUTES"),
                seconds=CONFIG_INI.getint("JWT","EXPIRES_SECONDS"),
            ),
            "iat": datetime.now(timezone.utc),
            "sub": user_id,
            "admin": admin
        }
        return jwt.encode(
            payload,
            secret_key,
            algorithm='HS384'
        )
    except Exception as e:
        return e

def hash_secret(str_to_hash, secret_key):
    """Generates a hash"""
    return hashlib.sha1((str_to_hash + secret_key).encode()).hexdigest()

def clear_session_data(login_redirect=False):
    """Clear the session data and cookies"""
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    endpoint = 'authentication.login' if login_redirect else 'toplevel.home'
    resp = make_response(redirect(url_for(endpoint)))
    resp.set_cookie('rememberme', expires=0)
    resp.set_cookie('jwt', expires=0)
    return resp

def display_user(username):
    if "@" in username:
        username = username.split("@")[0]
    return username
