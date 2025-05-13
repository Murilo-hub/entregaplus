def get_user_ip():
    from flask import request
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        ip = request.environ['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.remote_addr
    return ip
