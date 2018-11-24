class DefaultConfig(object):
    """
    Flask默认配置
    """
    # 日志
    LOGGING_LEVEL = 'DEBUG'
    LOGGING_FILE_DIR = '/Users/delron/Desktop/logs'
    LOGGING_FILE_MAX_BYTES = 300 * 1024 * 1024
    LOGGING_FILE_BACKUP = 10

    # flask-sqlalchemy使用的参数
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/toutiao'  # 数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 追踪数据的修改信号

    # redis
    class REDIS:
        SMS_CODE = 'redis://127.0.0.1:6379/1'

    # 限流服务redis
    RATELIMIT_STORAGE_URL = 'redis://127.0.0.1:6379/0'
    RATELIMIT_STRATEGY = 'moving-window'
    # RATELIMIT_DEFAULT = ['200/hour;1000/day']

    # JWT
    JWT_SECRET = 'TPmi4aLWRbyVq8zu9v82dWYW17/z+UvRnYTt4P6fAXA'
    JWT_EXPIRES_DAY = 1


class CeleryConfig(object):
    """
    Celery默认配置
    """
    broker_url = 'amqp://admin:rabbitmq@localhost:5672/delron'

    task_routes = {
        'sms.*': {'queue': 'sms'},
    }

    # 阿里短信服务
    DYSMS_ACCESS_KEY_ID = ''
    DYSMS_ACCESS_KEY_SECRET = ''