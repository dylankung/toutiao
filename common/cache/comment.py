from sqlalchemy.orm import load_only, joinedload
from sqlalchemy import func
from flask_restful import marshal, fields
import time

from models import db
from models.user import User
from models.news import Comment
from toutiao.main import redis_cli
from . import constants


comment_fields = {
    'com_id': fields.Integer(attribute='id'),
    'aut_id': fields.Integer(attribute='user_id'),
    'aut_name': fields.String(attribute='user.name'),
    'aut_photo': fields.String(attribute='user.profile_photo', default=''),
    'like_count': fields.Integer(attribute='like_count'),
    'reply_count': fields.Integer(attribute='reply_count'),
    'pubdate': fields.DateTime(attribute='ctime', dt_format='iso8601'),
    'content': fields.String(attribute='content'),
    'is_top': fields.Integer(attribute='is_top')
}


comment_cache_fields = {
    'com_id': fields.Integer(attribute='com_id'),
    'aut_id': fields.Integer(attribute='aut_id'),
    'aut_name': fields.String(attribute='aut_name'),
    'aut_photo': fields.String(attribute='aut_photo'),
    'like_count': fields.Integer(attribute='like_count'),
    'reply_count': fields.Integer(attribute='reply_count'),
    'pubdate': fields.String(attribute='pubdate'),
    'content': fields.String(attribute='content'),
    'is_top': fields.Integer(attribute='is_top')
}


def _get_comm_from_cache(article_id, offset, limit):
    """
    从缓存redis中读取评论数据
    :param article_id: 文章id
    :param offset: 起始的评论id
    :param limit: 读取的数量
    :return: list[{comment}, {}...]
    """
    r_comm_cache = redis_cli['comm_cache']
    key = 'art:{}:comm'.format(article_id)

    if offset is None:
        # 从头开始取
        ret = r_comm_cache.zrevrange(key, 0, limit - 1)
    else:
        ret = r_comm_cache.zrevrangebyscore(key, offset-1, 0, 0, limit-1)

    results = []
    if ret:
        for comment_id in ret:
            comment = r_comm_cache.hgetall('comm:{}'.format(comment_id))
            if not comment:
                continue
            # comment = {
            #     'com_id': 1,
            #     'aut_id': 0,
            #     'aut_name': '',
            #     'aut_photo': '',
            #     'like_count': 0,
            #     'reply_count': 0,
            #     'pubdate': '',
            #     'content': '',
            #     'is_top': False
            # }
            results.append(marshal(comment, comment_cache_fields))

    return results


def _get_comm_from_db(article_id, offset, limit):
    """
    从mysql中查询评论数据
    :param article_id: 评论所属的文章id
    :param offset: 偏移量（值是评论id，根据评论id偏移）
    :param limit: 读取数量
    :return: [{comment}, ...]  评论结果列表
    """
    results = []  # 评论结果数据
    new_cache = {}  # 构造的缓存数据

    # 通过双字段排序将置顶放在结果前列
    # 如果offset为None，不做偏移
    if offset is None:
        comments = Comment.query.options(joinedload(Comment.user, innerjoin=True)
                                         .load_only(User.name, User.profile_photo)) \
            .filter(Comment.article_id == article_id,
                    Comment.parent_id == None,
                    Comment.status == Comment.STATUS.APPROVED) \
            .order_by(Comment.is_top.desc(), Comment.id.desc()).limit(limit).all()
    else:
        comments = Comment.query.options(joinedload(Comment.user, innerjoin=True)
                                         .load_only(User.name, User.profile_photo)) \
            .filter(Comment.id < offset,
                    Comment.article_id == article_id,
                    Comment.parent_id == None,
                    Comment.status == Comment.STATUS.APPROVED) \
            .order_by(Comment.is_top.desc(), Comment.id.desc()).limit(limit).all()

    if comments:

        r_comm_cache = redis_cli['comm_cache']
        pl = r_comm_cache.pipeline()

        for comment in comments:
            # 处理序列化字段
            comment_format = marshal(comment, comment_fields)

            if not (offset is not None and comment.is_top):
                results.append(comment_format)

            # 构造缓存数据
            new_cache[comment.id] = constants.COMMENTS_CACHE_MAX_SCORE+comment.id if comment.is_top else comment.id
            pl.hmset('comm:{}'.format(comment.id), comment_format)

        if new_cache:
            pl.zadd('art:{}:comm'.format(article_id), new_cache)
        pl.execute()

    return results


def get_comments_by_article(article_id, offset, limit):
    """
    获取文章的评论
    :param article_id: 文章id
    :param offset: 获取评论的偏移起始
    :param limit: 获取的评论数量
    :return: {
            'results': [
                {
                    'com_id': 0,
                    'aut_id': 0,
                    'aut_name': '',
                    'aut_photo': '',
                    'like_count': 0,
                    'reply_count': 0,
                    'pubdate': '',
                    'content': ''
                }
            ],
            'total_count': 0,
            'last_id': 0,
            'end_id': 0,
        }
    """
    r_comm_cache = redis_cli['comm_cache']
    pl = r_comm_cache.pipeline()
    timestamp = time.time()

    # 构造返回值
    result = {
        'results': [],
        'total_count': 0,
        'last_id': None,
        'end_id': None
    }

    # 评论的缓存统计数据
    figure = r_comm_cache.hgetall('art:{}:comm:figure'.format(article_id))

    if not figure:
        # 未缓存
        # 判断是否存在评论
        end_comment = Comment.query.options(load_only(Comment.id)) \
            .filter(Comment.article_id == article_id,
                    Comment.parent_id == None,
                    Comment.status == Comment.STATUS.APPROVED) \
            .order_by(Comment.is_top, Comment.id).limit(1).first()
        if end_comment is None:
            # 没有评论数据
            # 设置缓存
            pl.zadd('art:comm', {article_id: timestamp})
            pl.hset('art:{}:comm:figure'.format(article_id), 'count', 0)
            pl.execute()
            return result
        else:
            end_id = end_comment.id
            ret = db.session.query(func.count(Comment.id)) \
                .filter(Comment.article_id == article_id,
                        Comment.parent_id == None,
                        Comment.status == Comment.STATUS.APPROVED).first()
            total_count = ret[0]

            result['total_count'] = total_count
            result['end_id'] = end_id

            pl.zadd('art:comm', {article_id: timestamp})
            pl.hmset('art:{}:comm:figure'.format(article_id), {'count': total_count, 'end_id': end_id})
            pl.execute()

            # 判断请求的offset是否越界
            if offset is not None and offset <= end_id:
                return result
            else:
                ret = _get_comm_from_db(article_id, offset, limit)
                if ret:
                    result['results'].extend(ret)
                    result['last_id'] = ret[-1]['com_id']
                return result
    else:
        # 已缓存
        total_count = int(figure['count'])  # 评论总数
        end_id = int(figure['end_id'])  # 最后一个评论id
        if total_count == 0:
            return result

        result['total_count'] = total_count
        result['end_id'] = end_id

        if offset is not None and offset <= end_id:
            return result

        # 缓存了的总数量
        cache_count = r_comm_cache.zcard('art:{}:comm'.format(article_id))
        cache_count = int(cache_count)

        if cache_count >= total_count:
            # 全部从redis取
            ret = _get_comm_from_cache(article_id, offset, limit)
            if ret:
                result['results'].extend(ret)
                result['last_id'] = ret[-1]['com_id']
        else:
            # redis与mysql都有
            ret = _get_comm_from_cache(article_id, offset, limit)
            if len(ret) >= limit:
                # 在redis中取了足够的数据
                result['results'].extend(ret)
                result['last_id'] = ret[-1]['com_id']
            else:
                # 需要在mysql中取数据
                ret = _get_comm_from_db(article_id, offset, limit)
                if ret:
                    result['results'].extend(ret)
                    result['last_id'] = ret[-1]['com_id']

    return result


# #####################################################################################################
# 以下为评论回复
# #####################################################################################################


def _get_reply_from_cache(comment_id, offset, limit):
    """
    从缓存redis中读取评论回复数据
    :param comment_id: 评论id
    :param offset: 起始的评论id
    :param limit: 读取的数量
    :return: list[{comment}, {}...]
    """
    r_comm_cache = redis_cli['comm_cache']
    key = 'comm:{}:reply'.format(comment_id)

    if offset is None:
        # 从头开始取
        ret = r_comm_cache.zrevrange(key, 0, limit - 1)
    else:
        ret = r_comm_cache.zrevrangebyscore(key, offset-1, 0, 0, limit-1)

    results = []
    if ret:
        for comment_id in ret:
            comment = r_comm_cache.hgetall('comm:{}'.format(comment_id))
            if not comment:
                continue
            # comment = {
            #     'com_id': 1,
            #     'aut_id': 0,
            #     'aut_name': '',
            #     'aut_photo': '',
            #     'like_count': 0,
            #     'reply_count': 0,
            #     'pubdate': '',
            #     'content': '',
            #     'is_top': False
            # }
            results.append(marshal(comment, comment_cache_fields))

    return results


def _get_reply_from_db(comment_id, offset, limit):
    """
    从mysql中查询评论回复数据
    :param comment_id: 回复所属的评论id
    :param offset: 偏移量（值是评论id，根据评论id偏移）
    :param limit: 读取数量
    :return: [{comment}, ...]  评论结果列表
    """
    results = []  # 评论结果数据
    new_cache = {}  # 构造的缓存数据

    # 通过双字段排序将置顶放在结果前列
    # 如果offset为None，不做偏移
    if offset is None:
        comments = Comment.query.options(joinedload(Comment.user, innerjoin=True)
                                         .load_only(User.name, User.profile_photo)) \
            .filter(Comment.parent_id == comment_id,
                    Comment.status == Comment.STATUS.APPROVED) \
            .order_by(Comment.is_top.desc(), Comment.id.desc()).limit(limit).all()
    else:
        comments = Comment.query.options(joinedload(Comment.user, innerjoin=True)
                                         .load_only(User.name, User.profile_photo)) \
            .filter(Comment.id < offset,
                    Comment.parent_id == comment_id,
                    Comment.status == Comment.STATUS.APPROVED) \
            .order_by(Comment.is_top.desc(), Comment.id.desc()).limit(limit).all()

    if comments:

        r_comm_cache = redis_cli['comm_cache']
        pl = r_comm_cache.pipeline()

        for comment in comments:
            # 处理序列化字段
            comment_format = marshal(comment, comment_fields)

            if not (offset is not None and comment.is_top):
                results.append(comment_format)

            # 构造缓存数据
            new_cache[comment.id] = constants.COMMENTS_CACHE_MAX_SCORE+comment.id if comment.is_top else comment.id
            pl.hmset('comm:{}'.format(comment.id), comment_format)

        if new_cache:
            pl.zadd('comm:{}:reply'.format(comment_id), new_cache)
        pl.execute()

    return results


def get_reply_by_comment(comment_id, offset, limit):
    """
    获取评论的回复
    :param comment_id: 评论id
    :param offset: 获取评论的偏移起始
    :param limit: 获取的评论数量
    :return: {
            'results': [
                {
                    'com_id': 0,
                    'aut_id': 0,
                    'aut_name': '',
                    'aut_photo': '',
                    'like_count': 0,
                    'reply_count': 0,
                    'pubdate': '',
                    'content': ''
                }
            ],
            'total_count': 0,
            'last_id': 0,
            'end_id': 0,
        }
    """
    r_comm_cache = redis_cli['comm_cache']
    pl = r_comm_cache.pipeline()
    timestamp = time.time()

    # 构造返回值
    result = {
        'results': [],
        'total_count': 0,
        'last_id': None,
        'end_id': None
    }

    # 评论的缓存统计数据
    figure = r_comm_cache.hgetall('comm:{}:reply:figure'.format(comment_id))

    if not figure:
        # 未缓存
        # 判断是否存在评论
        end_comment = Comment.query.options(load_only(Comment.id)) \
            .filter(Comment.parent_id == comment_id,
                    Comment.status == Comment.STATUS.APPROVED) \
            .order_by(Comment.is_top, Comment.id).limit(1).first()
        if end_comment is None:
            # 没有评论数据
            # 设置缓存
            pl.zadd('comm:reply', {comment_id: timestamp})
            pl.hset('comm:{}:reply:figure'.format(comment_id), 'count', 0)
            pl.execute()
            return result
        else:
            end_id = end_comment.id
            ret = db.session.query(func.count(Comment.id)) \
                .filter(Comment.parent_id == comment_id,
                        Comment.status == Comment.STATUS.APPROVED).first()
            total_count = ret[0]

            result['total_count'] = total_count
            result['end_id'] = end_id

            pl.zadd('comm:reply', {comment_id: timestamp})
            pl.hmset('comm:{}:reply:figure'.format(comment_id), {'count': total_count, 'end_id': end_id})
            pl.execute()

            # 判断请求的offset是否越界
            if offset is not None and offset <= end_id:
                return result
            else:
                ret = _get_reply_from_db(comment_id, offset, limit)
                if ret:
                    result['results'].extend(ret)
                    result['last_id'] = ret[-1]['com_id']
                return result
    else:
        # 已缓存
        total_count = int(figure['count'])  # 评论总数
        end_id = int(figure['end_id'])  # 最后一个评论id
        if total_count == 0:
            return result

        result['total_count'] = total_count
        result['end_id'] = end_id

        if offset is not None and offset <= end_id:
            return result

        # 缓存了的总数量
        cache_count = r_comm_cache.zcard('comm:{}:reply'.format(comment_id))
        cache_count = int(cache_count)

        if cache_count >= total_count:
            # 全部从redis取
            ret = _get_reply_from_cache(comment_id, offset, limit)
            if ret:
                result['results'].extend(ret)
                result['last_id'] = ret[-1]['com_id']
        else:
            # redis与mysql都有
            ret = _get_reply_from_cache(comment_id, offset, limit)
            if len(ret) >= limit:
                # 在redis中取了足够的数据
                result['results'].extend(ret)
                result['last_id'] = ret[-1]['com_id']
            else:
                # 需要在mysql中取数据
                ret = _get_reply_from_db(comment_id, offset, limit)
                if ret:
                    result['results'].extend(ret)
                    result['last_id'] = ret[-1]['com_id']

    return result


def determine_comment_exists(comment_id):
    """
    判断评论或评论回复是否存在
    :param comment_id: 评论id（或回复id）
    :return: bool
    """
    r_comm_cache = redis_cli['comm_cache']
    ret = r_comm_cache.exists('comm:{}'.format(comment_id))
    if ret > 0:
        return True
    else:
        ret = db.session.query(func.count(Comment.id)).filter_by(id=comment_id, status=Comment.STATUS.APPROVED).first()
        return True if ret[0] > 0 else False


def update_comment_liking_count(comment_id, increment=1):
    """
    更新缓存中评论的点赞数量
    :param comment_id: 评论id(或回复id）
    :param increment: 增量
    """
    r_comm_cache = redis_cli['comm_cache']
    key = 'comm:{}'.format(comment_id)
    exist = r_comm_cache.exists(key)
    if exist:
        r_comm_cache.hincrby(key, 'like_count', increment)


def update_comment_reply_count(comment_id, increment=1):
    """
    更新缓存中评论的回复数量
    :param comment_id:  评论id
    :param increment: 增量
    """
    r_comm_cache = redis_cli['comm_cache']
    key = 'comm:{}'.format(comment_id)
    exist = r_comm_cache.exists(key)
    if exist:
        r_comm_cache.hincrby(key, 'reply_count', increment)