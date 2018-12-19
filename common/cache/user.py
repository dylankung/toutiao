from flask import current_app
import time
from sqlalchemy.orm import load_only
from sqlalchemy import func
from flask_restful import marshal, fields

from models.user import User, Relation
from models import db


user_fields_db = {
    'mobile': fields.String(attribute='mobile'),
    'name': fields.String(attribute='name'),
    'photo': fields.String(attribute='profile_photo'),
    'is_media': fields.Integer(attribute='is_media'),
    'intro': fields.String(attribute='introduction'),
    'certi': fields.String(attribute='certificate'),
    'art_count': fields.Integer(attribute='article_count'),
    'follow_count': fields.Integer(attribute='following_count'),
    'fans_count': fields.Integer(attribute='fans_count'),
    'like_count': fields.Integer(attribute='like_count')
}


user_fields_cache = {
    'mobile': fields.String(attribute='mobile'),
    'name': fields.String(attribute='name'),
    'photo': fields.String(attribute='photo'),
    'is_media': fields.Integer(attribute='is_media'),
    'intro': fields.String(attribute='intro'),
    'certi': fields.String(attribute='certi'),
    'art_count': fields.Integer(attribute='art_count'),
    'follow_count': fields.Integer(attribute='follow_count'),
    'fans_count': fields.Integer(attribute='fans_count'),
    'like_count': fields.Integer(attribute='like_count')
}


def _generate_user_cache_data(user_id, user=None):
    """
    从数据库查询用户数据
    :param user_id: 用户id
    :param user: 已存在的用户数据
    :return:
    """
    if user is None:
        user = User.query.options(load_only(User.name,
                                            User.mobile,
                                            User.profile_photo,
                                            User.is_media,
                                            User.introduction,
                                            User.certificate,
                                            User.article_count,
                                            User.following_count,
                                            User.fans_count,
                                            User.like_count)) \
            .filter_by(id=user_id).first()
    user.profile_photo = user.profile_photo or ''
    user.introduction = user.introduction or ''
    user.certificate = user.certificate or ''
    user_data = marshal(user, user_fields_db)
    return user_data


def save_user_data_cache(user_id, user=None):
    """
    设置用户数据缓存
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()
    ret = r.zadd('user', {user_id: timestamp})
    if ret > 0:
        # This user cache data did not exist previously.
        user_data = _generate_user_cache_data(user_id, user)
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


def get_user(user_id):
    """
    获取用户数据
    :param user_id: 用户id
    :return:
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()

    ret = r.hgetall('user:{}'.format(user_id))
    if ret:
        # hit cache
        r.zadd('user', {user_id: timestamp})
        user_data = marshal(ret, user_fields_cache)
    else:
        user_data = _generate_user_cache_data(user_id)
        pl = r.pipeline()
        pl.zadd('user', {user_id: timestamp})
        pl.hmset('user:{}'.format(user_id), user_data)
        pl.execute()

    return user_data


def update_user_following(user_id, target_user_id, increment=1):
    """
    更新用户的关注缓存数据
    :param user_id: 操作用户
    :param target_user_id: 被关注的目标用户
    :param increment: 增量
    :return:
    """
    User.query.filter_by(id=target_user_id).update({'fans_count': User.fans_count + increment})
    User.query.filter_by(id=user_id).update({'following_count': User.following_count + increment})
    db.session.commit()

    r = current_app.redis_cli['user_cache']
    timestamp = time.time()

    pl = r.pipeline()

    # Update user following count
    key = 'user:{}'.format(user_id)
    exist = r.exists(key)
    if exist:
        pl.hincrby(key, 'follow_count', increment)

    # Update user following user id list
    key = 'user:{}:following'.format(user_id)
    exist = r.exists(key)
    if exist:
        if increment > 0:
            pl.zadd(key, {target_user_id, timestamp})
        else:
            pl.zrem(key, target_user_id)

    # Update target user followers(fans) count
    key = 'user:{}'.format(target_user_id)
    exist = r.exists(key)
    if exist:
        pl.hincrby(key, 'fans_count', increment)

    # Update target user followers(fans) user id list
    key = 'user:{}:fans'.format(target_user_id)
    exist = r.exists(key)
    if exist:
        if increment > 0:
            pl.zadd(key, {user_id, timestamp})
        else:
            pl.zrem(key, user_id)

    pl.execute()


def get_user_followings(user_id):
    """
    获取用户的关注列表
    :param user_id:
    :return:
    """
    r = current_app.redis_cli['user_cache']
    ret = r.zrevrange('user:{}:following'.format(user_id), 0, -1)
    if ret:
        return ret

    ret = r.hget('user:{}'.format(user_id), 'follow_count')
    if ret is not None and int(ret) == 0:
        return []

    ret = Relation.query.options(load_only(Relation.target_user_id, Relation.utime))\
        .fitler_by(user_id=user_id, relation=Relation.RELATION.FOLLOW)\
        .order_by(Relation.utime.desc()).all()

    followings = []
    cache = {}
    for relation in ret:
        # In order to be consistent with cache data type.
        followings.append(str(relation.target_user_id))
        cache[relation.target_user_id] = relation.utime.timestamp()

    if cache:
        timestamp = time.time()
        pl = r.pipeline()
        pl.zadd('user:following', {user_id: timestamp})
        pl.zadd('user:{}:following'.format(user_id), cache)
        pl.execute()

    return followings


def determine_user_follows_target(user_id, target_user_id):
    """
    判断用户是否关注了目标用户
    :param user_id:
    :param target_user_id: 被关注的用户id
    :return:
    """
    followings = get_user_followings(user_id)

    return str(target_user_id) in followings
