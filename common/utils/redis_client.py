from redis import Redis


def create_redis_clients(flask_app):
    """
    创建redis客户端
    :param flask_app: Flask应用对象
    :return: dict redis客户端对象的字典
    """
    return {
        'sms_code': Redis.from_url(flask_app.config['REDIS'].SMS_CODE),
        'read_his': Redis.from_url(flask_app.config['REDIS'].READING_HISTORY),
        'cache': Redis.from_url(flask_app.config['REDIS'].CACHE)
    }