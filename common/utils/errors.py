from redis.exceptions import RedisError


def log_exception(sender, exception, **extra):
    """
    记录异常日志
    """
    if isinstance(exception, RedisError):
        sender.logger.error('[Redis] {}'.format(exception))


errors = {
    'RedisError': {
        'message': 'Service unavailable.',
        'status': 507
    }
}