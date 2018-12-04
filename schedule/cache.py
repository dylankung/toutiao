from common import redis_cli

LIMIT = 10000


def clear_user_data_cache():
    """
    清理用户数据缓存，仅保留有限的最近活跃用户
    """
    r = redis_cli['user_cache']
    size = r.zcard('recent:')
    if size <= LIMIT:
        return

    end_index = size - LIMIT
    user_id_li = r.zrange('recent:', 0, end_index-1)
    user_cache_keys = []
    for user_id in user_id_li:
        user_cache_keys.append('recent:{}'.format(user_id.decode()))
    r.delete(*user_cache_keys)
    r.zrem('recent:', *user_id_li)



