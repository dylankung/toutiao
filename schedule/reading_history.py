import logging

from common import redis_cli

logger = logging.getLogger('apscheduler')


def save_reading_history_to_mysql():
    """
    同步用户阅读历史 from redis to mysql
    """
    print('hhhhhhh')
    logger.info('save reading history to mysql called.')
