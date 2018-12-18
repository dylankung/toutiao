from flask import current_app
import time
from sqlalchemy.orm import load_only
from sqlalchemy import func

from models.user import User
from models import db


def save_user_data_cache(user_id, user=None):
    """
    设置用户数据缓存
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()
    ret = r.zadd('user', {user_id: timestamp})
    if ret > 0:
        if user is None:
            user = User.query.options(load_only(User.name, User.mobile, User.profile_photo)) \
                .filter_by(id=user_id).first()
        user_data = {
            'mobile': user.mobile,
            'name': user.name,
            'photo': user.profile_photo
        }
        r.hmset('user:{}'.format(user_id), user_data)


def determine_user_exists(user_id):
    """
    判断用户是否存在
    :param user_id: 用户id
    :return: bool
    """
    r = current_app.redis_cli['user_cache']
    ret = r.exists('user:{}'.format(user_id))
    if ret > 0:
        return True
    else:
        ret = db.session.query(func.count(User.id)).filter_by(id=user_id).first()
        return True if ret[0] > 0 else False
