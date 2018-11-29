import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import DBAPIError
import grpc

from utils.logging import create_logger
from utils.converters import register_converters
from utils.errors import handle_redis_error, handler_mysql_error
from utils.middlewares import jwt_authentication


# redis连接
redis_cli = {}

# rpc
rpc_cli = None

# 限流器
limiter = Limiter(key_func=get_remote_address)


def create_app(config, enable_config_file=False):
    """
    创建应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: Flask应用
    """
    app = Flask(__name__)
    app.config.from_object(config)
    if enable_config_file:
        app.config.from_envvar('TOUTIAO_WEB_SETTINGS', silent=True)

    # 限流器
    limiter.init_app(app)

    # 配置日志
    create_logger(app)

    # 注册url转换器
    register_converters(app)

    # redis
    global redis_cli
    redis_cli['sms_code'] = Redis.from_url(app.config['REDIS'].SMS_CODE)
    redis_cli['read_his'] = Redis.from_url(app.config['REDIS'].READING_HISTORY)
    redis_cli['cache'] = Redis.from_url(app.config['REDIS'].CACHE)

    # rpc
    global rpc_cli
    rpc_cli = grpc.insecure_channel(app.config['RPC_SERVER'])

    # 数据库连接初始化
    from models import db
    db.init_app(app)

    # 添加异常处理
    app.register_error_handler(RedisError, handle_redis_error)
    app.register_error_handler(DBAPIError, handler_mysql_error)

    # 添加请求钩子
    app.before_request(jwt_authentication)

    # 注册用户模块蓝图
    from .resources.user import user_bp
    app.register_blueprint(user_bp)

    # 注册新闻模块蓝图
    from .resources.news import news_bp
    app.register_blueprint(news_bp)

    return app
