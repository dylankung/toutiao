from sqlalchemy.orm import joinedload, load_only
from flask_restful import fields, marshal
import pickle
import time
from sqlalchemy import func
from flask import current_app
from redis.exceptions import RedisError

from models.news import Article, ArticleStatistic
from models.user import User
from models import db
from . import user as cache_user
from . import constants


# article_info_fields_redis = {
#     'title': fields.String(attribute=b'title'),
#     'aut_id': fields.Integer(attribute=b'aut_id'),
#     # 'aut_name': fields.String(attribute=b'aut_name'),
#     'comm_count': fields.Integer(attribute=b'comm_count'),
#     'pubdate': fields.String(attribute=b'pubdate'),
#     'is_top': fields.Integer(attribute=b'is_top'),
#     'ch_id': fields.Integer(attribute=b'ch_id')
# }

article_info_fields_db = {
    'title': fields.String(attribute='title'),
    'aut_id': fields.Integer(attribute='user_id'),
    # 'aut_name': fields.String(attribute='user.name'),
    'comm_count': fields.Integer(attribute='comment_count'),
    'pubdate': fields.DateTime(attribute='ctime', dt_format='iso8601'),
    'like_count': fields.Integer(attribute='statistic.like_count'),
    'collect_count': fields.Integer(attribute='statistic.collect_count'),
    'ch_id': fields.Integer(attribute='channel_id')
}


def get_channel_top_articles(channel_id):
    """
    获取指定频道的置顶文章id
    :param channel_id: 频道id
    :return: [article_id, ...]
    """
    r = current_app.redis_cli['art_cache']

    ret = r.zrevrange('ch:{}:art:top'.format(channel_id), 0, -1)
    if not ret:
        return []
    else:
        return [int(article_id) for article_id in ret]


def get_channel_top_articles_count(channel_id):
    """
    获取指定频道的置顶文章的数量
    :param channel_id: 频道id
    :return: int
    """
    r = current_app.redis_cli['art_cache']

    ret = r.zcard('ch:{}:art:top'.format(channel_id))
    return ret


def get_article_info(article_id):
    """
    获取文章
    :param article_id: 文章id
    :return: {}
    """
    r = current_app.redis_cli['art_cache']
    timestamp = time.time()

    # 从缓存中查询
    # TODO 后续可能只几个获取指定字段
    article = r.hgetall('art:{}:info'.format(article_id))
    if article:
        # 更新文章最新使用时间
        r.zadd('art', {article_id: timestamp})
        # 不能处理bytes类型
        # article_formatted = marshal(article, article_info_fields_redis)
        article_formatted = dict(
            art_id=article_id,
            title=article[b'title'].decode(),
            aut_id=int(article[b'aut_id']),
            # aut_name=article[b'aut_name'].decode(),
            comm_count=int(article[b'comm_count']),
            pubdate=article[b'pubdate'].decode(),
            is_top=int(article[b'is_top']),
            cover=pickle.loads(article[b'cover']),
            like_count=int(article[b'like_count']),
            collect_count=int(article[b'collect_count']),
            ch_id=int(article[b'ch_id'])
        )
    else:
        article = Article.query.options(load_only(Article.id, Article.title, Article.user_id, Article.channel_id,
                                                  Article.cover, Article.ctime, Article.comment_count),
                                        joinedload(Article.statistic, innerjoin=True).load_only(ArticleStatistic.like_count,
                                                                                                ArticleStatistic.collect_count))\
            .filter_by(id=article_id, status=Article.STATUS.APPROVED).first()
        if article is None:
            return

        article_formatted = marshal(article, article_info_fields_db)

        # 判断是否置顶
        rank = r.zrank('channel:{}:art:top'.format(article.channel_id), article_id)
        if rank is None:
            article_formatted['is_top'] = 0
        else:
            article_formatted['is_top'] = 1

        # 设置缓存
        article_formatted['cover'] = pickle.dumps(article.cover)

        pl = r.pipeline()
        pl.zadd('art', {article_id: timestamp})
        pl.hmset('art:{}:info'.format(article_id), article_formatted)
        pl.execute()

        article_formatted['art_id'] = article_id
        article_formatted['cover'] = article.cover

    # 获取作者名
    author = cache_user.get_user(article_formatted['aut_id'])
    article_formatted['aut_name'] = author['name']

    return article_formatted


def get_article_detail(article_id):
    """
    获取文章详情信息
    :param article_id: 文章id
    :return:
    """
    # 查询文章数据
    r = current_app.redis_cli['art_cache']
    article_bytes = r.get('art:{}:detail'.format(article_id))
    if article_bytes:
        # 使用缓存
        article_dict = pickle.loads(article_bytes)
    else:
        # 查询数据库
        article = Article.query.options(load_only(
            Article.id,
            Article.user_id,
            Article.title,
            Article.is_advertising,
            Article.ctime
        )).filter_by(id=article_id, status=Article.STATUS.APPROVED).first()

        article_fields = {
            'art_id': fields.Integer(attribute='id'),
            'title': fields.String(attribute='title'),
            'pubdate': fields.DateTime(attribute='ctime', dt_format='iso8601'),
            'content': fields.String(attribute='content.content'),
            'aut_id': fields.Integer(attribute='user_id'),
        }
        article_dict = marshal(article, article_fields)

        # 缓存
        article_cache = pickle.dumps(article_dict)
        try:
            r.setex('art:{}:detail'.format(article_id), constants.CACHE_ARTICLE_EXPIRE, article_cache)
        except RedisError:
            pass

    user = cache_user.get_user(article_dict['aut_id'])

    article_dict['aut_name'] = user['name']
    article_dict['aut_photo'] = user['photo']

    return article_dict


def update_article_comment_count(article_id, increment=1):
    """
    更新文章评论数量
    :param article_id: 文章id
    :param increment: 增量
    :return:
    """
    Article.query.filter_by(id=article_id).update({'comment_count': Article.comment_count + increment})
    db.session.commit()

    r = current_app.redis_cli['art_cache']
    key = 'art:{}:info'.format(article_id)
    exist = r.exists(key)

    if exist:
        r.hincrby(key, 'comm_count', increment)


def determine_article_exists(article_id):
    """
    判断文章是否存在
    :param article_id: 文章id
    :return: bool
    """
    r = current_app.redis_cli['art_cache']
    ret = r.exists('art:{}:info'.format(article_id))
    if ret > 0:
        return True
    else:
        ret = db.session.query(func.count(Article.id)).filter_by(id=article_id, status=Article.STATUS.APPROVED).first()
        return True if ret[0] > 0 else False


def update_article_collect_count(article_id, increment=1):
    """
    更新文章收藏数量
    :param article_id: 文章id
    :param increment: 增量
    :return:
    """
    ArticleStatistic.query.filter_by(id=article_id).update({'collect_count': ArticleStatistic.collect_count + increment})
    db.session.commit()

    r = current_app.redis_cli['art_cache']
    key = 'art:{}:info'.format(article_id)
    exist = r.exists(key)

    if exist:
        r.hincrby(key, 'collect_count', increment)


def update_article_liking_count(article_id, increment=1):
    """
    更新文章点赞数量
    :param article_id: 文章id
    :param increment: 增量
    :return:
    """
    ArticleStatistic.query.filter_by(id=article_id).update({'like_count': ArticleStatistic.like_count + increment})
    db.session.commit()

    r = current_app.redis_cli['art_cache']
    key = 'art:{}:info'.format(article_id)
    exist = r.exists(key)

    if exist:
        r.hincrby(key, 'like_count', increment)


def update_article_read_count(article_id):
    """
    更新文章阅读数
    :param article_id:
    :return:
    """
    ArticleStatistic.query.filter_by(id=article_id).update({'read_count': ArticleStatistic.read_count + 1})
    db.session.commit()

    r = current_app.redis_cli['art_cache']
    key = 'art:{}:info'.format(article_id)
    exist = r.exists(key)

    if exist:
        r.hincrby(key, 'read_count', 1)
