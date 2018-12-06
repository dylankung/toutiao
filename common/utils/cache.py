from flask import current_app
import time
from sqlalchemy.orm import load_only
import pickle

from models.user import User


def save_user_data_cache(user_id, user=None):
    """
    设置用户数据缓存
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()
    ret = r.zadd('recent:', {user_id: timestamp})
    if ret > 0:
        if user is None:
            user = User.query.options(load_only(User.name, User.mobile, User.profile_photo)) \
                .filter_by(id=user_id).first()
        user_data = {
            'mobile': user.mobile,
            'name': user.name,
            'photo': user.profile_photo
        }
        r.set('recent:{}'.format(user_id), pickle.dumps(user_data))
