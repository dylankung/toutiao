import pickle
from sqlalchemy.orm import load_only
from flask_restful import marshal, fields

from toutiao.main import redis_cli
from models.news import Channel


channel_fields = {
    'id': fields.Integer(attribute='id'),
    'name': fields.String(attribute='name')
}


def get_all_channels():
    """
    获取所有频道数据
    :return: [{'name': 'python', 'id': '123'}, {}]
    """
    r = redis_cli['art_cache']

    # 缓存取数据
    ret = r.get('channel')
    if ret:
        results = pickle.loads(ret)
        return results

    # 数据库查询
    results = []

    channels = Channel.query.options(load_only(Channel.id, Channel.name))\
        .filter(Channel.is_visible == True).order_by(Channel.sequence).all()

    if not channels:
        return results

    for channel in channels:
        results.append(marshal(channel, channel_fields))

    # 设置缓存
    r.set('channel', pickle.dumps(results))

    return results




