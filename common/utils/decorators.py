from flask import g
from functools import wraps
from sqlalchemy.orm import load_only

from cache.user import save_user_data_cache
from cache.permission import get_group_permission_ids

from models.system import MisAdministrator, MisPermission, MisGroupPermission, MisAdministratorGroup
from models import db


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


def mis_login_required(func):
    """
    mis用户必须认证通过装饰器
    使用方法：放在method_decorators中
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not g.administrator_id:
            return {'message': 'User must be authorized.'}, 401
        elif g.refresh_token:
            return {'message': 'Do not use refresh token.'}, 403
        else:
            return func(*args, **kwargs)

    return wrapper


def mis_permission_required(permission_code):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not g.administrator_id:
                return {'message': 'Administrator must be authorized.'}, 401
            elif g.refresh_token:
                return {'message': 'Do not use refresh token.'}, 403
            else:
                administrator = MisAdministrator.query.filter_by(id=g.administrator_id).first()
                if not administrator:
                    return {'message': 'Administrator does not exist.'}, 403
                # # test
                # test_perm = MisPermission.query.filter_by(code=permission_code, type=1).first()
                # if not test_perm:
                #     test_perm = MisPermission(name=permission_code, type=MisPermission.TYPE.API,
                #                               parent_id=0, code=permission_code, sequence=1)
                #     db.session.add(test_perm)
                #     db.session.commit()
                # group_perm = MisGroupPermission.query.filter_by(group_id=administrator.group_id,
                #                                                 permission_id=test_perm.id).first()
                # if not group_perm:
                #     group_perm = MisGroupPermission(group_id=administrator.group_id,
                #                                     permission_id=test_perm.id)
                #     db.session.add(group_perm)
                #     db.session.commit()
                # test end

                if administrator.group.status == MisAdministratorGroup.STATUS.DISABLE:
                    return {'message': 'Group status disable.'}, 403

                permission_ids = get_group_permission_ids(administrator.group_id)
                permissions = MisPermission.query.options(load_only(MisPermission.code))\
                    .filter_by(type=MisPermission.TYPE.API).filter(MisPermission.id.in_(permission_ids)).all()
                codes = [i.code for i in permissions]
                if permission_code not in codes:
                    return {'message': 'Permission denied.'}, 403
                return func(*args, **kwargs)

        return wrapper

    return decorator
