import jwt
from flask import current_app
from datetime import datetime, timedelta


def generate_jwt(payload):
    """
    生成jwt
    :param payload: dict 载荷
    :return: jwt
    """
    _payload = {'exp': datetime.utcnow() + timedelta(days=current_app.config['JWT_EXPIRES_DAY'])}
    _payload.update(payload)
    token = jwt.encode(_payload, current_app.config['JWT_SECRET'], algorithm='HS256')
    return token.decode()


def verify_jwt(token):
    """
    检验jwt
    :param token: jwt
    :return: dict payload
    """
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithm=['HS256'])
    except jwt.PyJWTError:
        payload = None
    return payload
