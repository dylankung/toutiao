import jwt
from flask import current_app


def generate_jwt(payload, expiry):
    """
    生成jwt
    :param payload: dict 载荷
    :param expiry: datetime 有效期
    :return: jwt
    """
    _payload = {'exp': expiry}
    _payload.update(payload)
    token = jwt.encode(_payload, current_app.config['JWT_SECRET'], algorithm='HS256')
    return token.decode()


def verify_jwt(token):
    """
    检验jwt
    :param token: jwt
    :return: dict: payload
    """
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithm=['HS256'])
    except jwt.PyJWTError:
        payload = None

    return payload
