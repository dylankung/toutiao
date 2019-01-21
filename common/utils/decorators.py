from flask import g
from functools import wraps

from cache.user import save_user_data_cache


def login_required(func):
    """
    用户必须登录装饰器
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user_id:
            return {'message': 'User must be authorized.'}, 401
        elif g.is_refresh_token:
            return {'message': 'Do not use refresh token.'}, 403
        else:
            # 设置或更新用户缓存
            save_user_data_cache(g.user_id)
            return func(*args, **kwargs)

    return wrapper


def validate_token_if_using(func):
    """
    如果Authorization中携带了Token，则检验token的有效性，否则放行
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.use_token and not g.user_id:
            return {'message': 'Token has some errors.'}, 401
        else:
            if g.user_id:
                # 设置或更新用户缓存
                save_user_data_cache(g.user_id)
            return func(*args, **kwargs)

    return wrapper


def verify_required(func):
    """
    用户必须实名认证通过装饰器
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.user_id:
            return {'message': 'User must be authorized.'}, 401
        elif g.is_refresh_token:
            return {'message': 'Do not use refresh token.'}, 403
        elif not g.is_verified:
            return {'message': 'User must be real info verified.'}, 403
        else:
            # 设置或更新用户缓存
            save_user_data_cache(g.user_id)
            return func(*args, **kwargs)

    return wrapper
