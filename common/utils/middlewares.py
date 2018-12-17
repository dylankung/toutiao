from flask import request, g

from .jwt_util import verify_jwt


def jwt_authentication():
    """
    根据jwt验证用户身份
    """
    g.user_id = None
    authorization = request.headers.get('Authorization')
    if authorization and 'Bearer' in authorization:
        token = authorization.strip()[7:]
        payload = verify_jwt(token)
        if payload:
            g.user_id = payload.get('user_id')
            g.refresh_token = payload.get('refresh')
