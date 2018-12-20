from flask import current_app
import pickle
from sqlalchemy.orm import load_only
from sqlalchemy import func

from models.notice import Announcement
from models import db


def get_announcements_by_page(page, per_page):
    """
    获取系统公告列表
    :param page: 页数
    :param per_page: 每页数量
    :return: total_count, []
    """
    r = current_app.redis_cli['notice_cache']

    key = 'announce'
    exist = r.exists(key)
    if exist:
        # Cache exists.
        total_count = r.zcard(key)
        ret = r.zrevrange(key, (page - 1) * per_page, page * per_page, withscores=True)
        if ret:
            results = []
            for announcement, announcement_id in ret:
                _announcement = pickle.loads(announcement)
                _announcement['id'] = int(announcement_id)
                results.append(_announcement)
            return total_count, results
        else:
            return total_count, []
    else:
        # No cache.
        ret = Announcement.query.options(load_only(Announcement.id, Announcement.pubtime, Announcement.title)) \
            .filter_by(status=Announcement.STATUS.PUBLISHED) \
            .order_by(Announcement.pubtime.desc()).all()

        results = []
        cache = {}
        for announcement in ret:
            _announcement = dict(
                pubdate=announcement.pubtime.strftime('%Y-%m-%dT%H:%M:%S'),
                title=announcement.title
            )
            cache[pickle.dumps(_announcement)] = announcement.id
            _announcement['id'] = announcement.id
            results.append(_announcement)

        if cache:
            r.zadd(key, cache)

        total_count = len(results)
        page_results = results[(page - 1) * per_page:page * per_page]

        return total_count, page_results


def determine_announcement_exist(announcement_id):
    """
    判断公告是否存在
    :param announcement_id:
    :return:
    """
    r = current_app.redis_cli['notice_cache']
    ret = r.exists('announce')
    if ret > 0:
        ret = r.zrangebyscore('announce', announcement_id, announcement_id)
        if ret:
            return True
        else:
            return False
    else:
        ret = db.session.query(func.count(Announcement.id))\
            .filter_by(id=announcement_id, status=Announcement.STATUS.PUBLISHED).first()
        return True if ret[0] > 0 else False


def get_announcement_detail(announcement_id):
    """
    获取公告内容
    :param announcement_id:
    :return:
    """
    r = current_app.redis_cli['notice_cache']
    key = 'announce:{}'.format(announcement_id)
    ret = r.get(key)
    if ret:
        announcement = pickle.loads(ret)
        announcement['id'] = announcement_id
        return announcement
    else:
        announcement = Announcement.query.options(load_only(Announcement.title, Announcement.content, Announcement.pubtime))\
            .filter_by(id=announcement_id, status=Announcement.STATUS.PUBLISHED).first()
        _announcement = {
            'pubdate': announcement.pubtime.strftime('%Y-%m-%dT%H:%M:%S'),
            'title': announcement.title,
            'content': announcement.content
        }
        r.set(key, pickle.dumps(_announcement))
        _announcement['id'] = announcement_id
        return _announcement



