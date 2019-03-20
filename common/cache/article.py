from sqlalchemy.orm import joinedload, load_only
from flask_restful import fields, marshal
import json
import time
from sqlalchemy import func
from flask import current_app
from redis.exceptions import RedisError, ConnectionError
from sqlalchemy.exc import SQLAlchemyError

from models.news import Article, ArticleStatistic, Attitude
from models.user import User
from models import db
from . import user as cache_user
from . import constants


# # 无用
# article_info_fields_redis = {
#     'title': fields.String(attribute=b'title'),
#     'aut_id': fields.Integer(attribute=b'aut_id'),
#     # 'aut_name': fields.String(attribute=b'aut_name'),
#     'comm_count': fields.Integer(attribute=b'comm_count'),
#     'pubdate': fields.String(attribute=b'pubdate'),
#     'is_top': fields.Integer(attribute=b'is_top'),
#     'ch_id': fields.Integer(attribute=b'ch_id')
# }


# # 无用
# def get_channel_top_articles_count(channel_id):
#     """
#     获取指定频道的置顶文章的数量
#     :param channel_id: 频道id
#     :return: int
#     """
#     r = current_app.redis_cli['art_cache']
#
#     ret = r.zcard('ch:{}:art:top'.format(channel_id))
#     return ret


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


class ArticleInfoCache(object):
    """
    文章基本信息缓存
    """
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

    def __init__(self, article_id):
        self.key = 'art:{}:info'.format(article_id)
        self.article_id = article_id

    def save(self):
        """
        保存文章缓存
        """
        rc = current_app.redis_cluster

        article = Article.query.options(load_only(Article.id, Article.title, Article.user_id, Article.channel_id,
                                                  Article.cover, Article.ctime, Article.comment_count),
                                        joinedload(Article.statistic, innerjoin=True).load_only(
                                            ArticleStatistic.like_count,
                                            ArticleStatistic.collect_count)) \
            .filter_by(id=self.article_id, status=Article.STATUS.APPROVED).first()
        if article is None:
            return

        article_formatted = marshal(article, self.article_info_fields_db)

        # 判断是否置顶
        try:
            article_formatted['is_top'] = ChannelTopArticlesStorage(article.channel_id).exists(self.article_id)
        except RedisError as e:
            current_app.logger.error(e)
            article_formatted['is_top'] = 0

        # 设置缓存
        article_formatted['cover'] = json.dumps(article.cover)

        # 补充exists字段，为防止缓存击穿使用
        # 参考下面exists方法说明
        article_formatted['exists'] = 1

        try:
            pl = rc.pipeline()
            pl.hmset(self.key, article_formatted)
            pl.expire(self.key, constants.ArticleInfoCacheTTL.get_val())
            results = pl.execute()
            if results[0] and not results[1]:
                rc.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)
        finally:
            del article_formatted['exists']

        article_formatted['art_id'] = self.article_id
        article_formatted['cover'] = article.cover

        return article_formatted

    def get(self):
        """
        获取文章
        :return: {}
        """
        rc = current_app.redis_cluster

        # 从缓存中查询
        # TODO 后续可能只获取几个指定字段
        try:
            article = rc.hgetall(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            article = None

        if article:
            # 不能处理bytes类型
            # article_formatted = marshal(article, article_info_fields_redis)
            article_formatted = dict(
                art_id=self.article_id,
                title=article[b'title'].decode(),
                aut_id=int(article[b'aut_id']),
                # aut_name=article[b'aut_name'].decode(),
                comm_count=int(article[b'comm_count']),
                pubdate=article[b'pubdate'].decode(),
                is_top=int(article[b'is_top']),
                cover=json.loads(article[b'cover']),
                like_count=int(article[b'like_count']),
                collect_count=int(article[b'collect_count']),
                ch_id=int(article[b'ch_id'])
            )
        else:
            article_formatted = self.save()

        # 获取作者名
        author = cache_user.UserProfileCache(article_formatted['aut_id']).get()
        article_formatted['aut_name'] = author['name']

        return article_formatted

    def exists(self):
        """
        判断文章是否存在
        :return: bool
        """
        rc = current_app.redis_cluster

        # 此处可使用的键有三种选择 user:{}:profile 或 user:{}:status 或 新建
        # status主要为当前登录用户，而profile不仅仅是登录用户，覆盖范围更大，所以使用profile
        try:
            exists = rc.hget(self.key, 'exists')
        except RedisError as e:
            current_app.logger.error(e)
            exists = None

        if exists is not None:
            exists = int(exists)

        if exists == 1:
            return True
        elif exists == 0:
            return False
        else:
            # 缓存中未查到
            ret = db.session.query(func.count(Article.id)).filter_by(id=self.article_id,
                                                                     status=Article.STATUS.APPROVED).first()
            if ret[0] > 0:
                try:
                    self.save()
                except SQLAlchemyError as e:
                    current_app.logger.error(e)
            else:
                try:
                    pl = rc.pipeline()
                    pl.hset(self.key, 'exists', 0)
                    pl.expire(self.key, constants.ArticleNotExistsCacheTTL.get_val())
                    results = pl.execute()
                    if results[0] and not results[1]:
                        pl.delete(self.key)
                except RedisError as e:
                    current_app.logger.error(e)
            return bool(ret[0])


class ChannelTopArticlesStorage(object):
    """
    频道置顶文章缓存
    使用redis持久保存
    """
    def __init__(self, channel_id):
        self.key = 'ch:{}:art:top'.format(channel_id)
        self.channel_id = channel_id

    def get(self):
        """
        获取指定频道的置顶文章id
        :return: [article_id, ...]
        """
        try:
            ret = current_app.redis_master.zrevrange(self.key, 0, -1)
        except ConnectionError as e:
            current_app.logger.error(e)
            ret = current_app.redis_slave.zrevrange(self.key, 0, -1)

        if not ret:
            return []
        else:
            return [int(article_id) for article_id in ret]

    def exists(self, article_id):
        """
        判断文章是否置顶
        :param article_id:
        :return:
        """
        try:
            rank = current_app.redis_master.zrank(self.key, article_id)
        except ConnectionError as e:
            current_app.logger.error(e)
            rank = current_app.redis_slave.zrank(self.key, article_id)

        return 0 if rank is None else 1


class ArticleDetailCache(object):
    """
    文章详细内容缓存
    """
    article_fields = {
        'art_id': fields.Integer(attribute='id'),
        'title': fields.String(attribute='title'),
        'pubdate': fields.DateTime(attribute='ctime', dt_format='iso8601'),
        'content': fields.String(attribute='content.content'),
        'aut_id': fields.Integer(attribute='user_id'),
        'ch_id': fields.Integer(attribute='channel_id'),
    }

    def __init__(self, article_id):
        self.key = 'art:{}:detail'.format(article_id)
        self.article_id = article_id

    def get(self):
        """
        获取文章详情信息
        :return:
        """
        # 查询文章数据
        rc = current_app.redis_cluster
        try:
            article_bytes = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            article_bytes = None

        if article_bytes:
            # 使用缓存
            article_dict = json.loads(article_bytes)
        else:
            # 查询数据库
            article = Article.query.options(load_only(
                Article.id,
                Article.user_id,
                Article.title,
                Article.is_advertising,
                Article.ctime,
                Article.channel_id
            )).filter_by(id=self.article_id, status=Article.STATUS.APPROVED).first()

            article_dict = marshal(article, self.article_fields)

            # 缓存
            article_cache = json.dumps(article_dict)
            try:
                rc.setex(self.key, constants.ArticleDetailCacheTTL.get_val(), article_cache)
            except RedisError:
                pass

        user = cache_user.UserProfileCache(article_dict['aut_id']).get()

        article_dict['aut_name'] = user['name']
        article_dict['aut_photo'] = user['photo']

        return article_dict


class ArticleUserAttitudeCache(object):
    """
    用户对文章态度的缓存，点赞或不喜欢
    """
    def __init__(self, user_id, article_id):
        self.user_id = user_id
        self.article_id = article_id
        self.key = 'user:{}:art:{}:liking'

    def get(self):
        """
        获取
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret is not None:
            ret = int(ret)
            return ret

        att = Attitude.query.options(load_only(Attitude.attitude)) \
            .filter_by(user_id=self.user_id, article_id=self.article_id).first()
        ret = att.attitude if att else -1

        try:
            ret = rc.setex(self.key, constants.ArticleUserNoAttitudeCacheTTL.get_val(), ret)
        except RedisError as e:
            current_app.logger.error(e)

        return ret

    def clear(self):
        """
        清除
        :return:
        """
        rc = current_app.redis_cluster
        try:
            rc.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)


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
