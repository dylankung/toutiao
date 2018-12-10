from common import redis_cli

USER_CACHE_LIMIT = 10000
COMMENT_CACHE_LIMIT = 10000
COMMENT_REPLY_CACHE_LIMIT = 10000


def clear_user_cache():
    """
    清理用户数据缓存，仅保留有限的最近活跃用户
    """
    r = redis_cli['user_cache']
    size = r.zcard('user')
    if size <= USER_CACHE_LIMIT:
        return

    end_index = size - USER_CACHE_LIMIT
    user_id_li = r.zrange('user', 0, end_index-1)
    user_cache_keys = []
    for user_id in user_id_li:
        user_cache_keys.append('user:{}'.format(user_id.decode()))
    pl = r.pipeline()
    pl.delete(*user_cache_keys)
    pl.zrem('user', *user_id_li)
    pl.execute()


def clear_comment_cache():
    """
    清理评论（包括评论回复）的缓存，仅保留有限的最热评论数据
    """
    r = redis_cli['comm_cache']

    # 清理文章评论
    size = r.zcard('comm')
    if size > COMMENT_CACHE_LIMIT:
        end_index = size - COMMENT_CACHE_LIMIT
        comment_id_li = r.zrange('comm', 0, end_index-1)
        comment_cache_keys = []
        for comment_id in comment_id_li:
            _id = comment_id.decode()
            comment_cache_keys.append('comm:{}'.format(_id))
            comment_cache_keys.append('comm:{}:figure'.format(_id))
        pl = r.pipeline()
        pl.delete(*comment_cache_keys)
        pl.zrem('comm', *comment_id_li)
        pl.execute()

    # 清理评论回复
    size = r.zcard('reply')
    if size > COMMENT_REPLY_CACHE_LIMIT:
        end_index = size - COMMENT_REPLY_CACHE_LIMIT
        comment_id_li = r.zrange('reply', 0, end_index - 1)
        comment_cache_keys = []
        for comment_id in comment_id_li:
            _id = comment_id.decode()
            comment_cache_keys.append('reply:{}'.format(_id))
            comment_cache_keys.append('reply:{}:figure'.format(_id))
        pl = r.pipeline()
        pl.delete(*comment_cache_keys)
        pl.zrem('reply', *comment_id_li)
        pl.execute()





