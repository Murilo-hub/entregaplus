from flask import request

def get_user_ip():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    elif request.environ.get('HTTP_X_REAL_IP'):
        ip = request.environ.get('HTTP_X_REAL_IP')
    else:
        ip = request.remote_addr
    return ip