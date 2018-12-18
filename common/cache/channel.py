import pickle
from sqlalchemy.orm import load_only
from flask_restful import marshal, fields
from sqlalchemy import func
from flask import current_app

from models.news import Channel
from models import db


channel_fields = {
    'id': fields.Integer(attribute='id'),
    'name': fields.String(attribute='name')
}


def get_all_channels():
    """
    获取所有频道数据
    :return: [{'name': 'python', 'id': '123'}, {}]
    """
    r = current_app.redis_cli['art_cache']

    # 缓存取数据
    ret = r.get('channel')
    if ret:
        results = pickle.loads(ret)
        return results

    # 数据库查询
    results = []
    cache = {}

    channels = Channel.query.options(load_only(Channel.id, Channel.name))\
        .filter(Channel.is_visible == True).order_by(Channel.sequence, Channel.id).all()

    if not channels:
        return results

    for channel in channels:
        results.append(marshal(channel, channel_fields))
        cache[channel.id] = channel.id

    # 设置缓存
    pl = r.pipeline()
    pl.set('channel', pickle.dumps(results))
    pl.zadd('channel:id', cache)
    pl.execute()

    return results


def determine_channel_exists(channel_id):
    """
    判断channel_id是否存在
    :param channel_id: 频道id
    :return: bool
    """
    r = current_app.redis_cli['art_cache']
    ret = r.exists('channel:id')
    if ret > 0:
        rank = r.zrank('channel:id', channel_id)
        if rank is None:
            return False
        else:
            return True
    else:
        ret = db.session.query(func.count(Channel.id)).filter_by(id=channel_id, is_visible=True).first()
        return True if ret[0] > 0 else False


def get_default_channels():
    """
    获取用户默认频道数据
    :return: [{'name': 'python', 'id': '123'}, {}]
    """
    r = current_app.redis_cli['art_cache']

    # 缓存取数据
    ret = r.get('channel:default')
    if ret:
        results = pickle.loads(ret)
        return results

    # 数据库查询
    results = []
    cache = {}

    channels = Channel.query.options(load_only(Channel.id, Channel.name))\
        .filter(Channel.is_default == True, Channel.is_visible == True).order_by(Channel.sequence, Channel.id).all()

    if not channels:
        return results

    for channel in channels:
        results.append(marshal(channel, channel_fields))
        cache[channel.id] = channel.id

    # 设置缓存
    r.set('channel:default', pickle.dumps(results))

    return results
