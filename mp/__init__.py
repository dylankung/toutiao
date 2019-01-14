from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from elasticsearch5 import Elasticsearch


# 限流器
limiter = Limiter(key_func=get_remote_address)


def create_flask_app(config, enable_config_file=False):
    """
    创建Flask应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: Flask应用
    """
    app = Flask(__name__)
    app.config.from_object(config)
    if enable_config_file:
        from utils import constants
        app.config.from_envvar(constants.GLOBAL_SETTING_ENV_NAME, silent=True)

    return app


def create_app(config, enable_config_file=False):
    """
    创建应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: 应用
    """
    app = create_flask_app(config, enable_config_file)

    # 限流器
    limiter.init_app(app)

    # 配置日志
    from utils.logging import create_logger
    create_logger(app)

    # 注册url转换器
    from utils.converters import register_converters
    register_converters(app)

    # redis
    from utils.redis_client import create_redis_clients
    app.redis_cli = create_redis_clients(app)

    # Elasticsearch
    app.es = Elasticsearch(
        app.config['ES'],
        # sniff before doing anything
        sniff_on_start=True,
        # refresh nodes after a node fails to respond
        sniff_on_connection_fail=True,
        # and also every 60 seconds
        sniffer_timeout=60
    )

    # MySQL数据库连接初始化
    from models import db
    db.init_app(app)

    # 添加异常处理
    from utils.errors import handle_redis_error, handler_mysql_error
    app.register_error_handler(RedisError, handle_redis_error)
    app.register_error_handler(SQLAlchemyError, handler_mysql_error)

    # 添加请求钩子
    from utils.middlewares import jwt_authentication
    app.before_request(jwt_authentication)

    # 注册用户模块蓝图
    from .resources.user import user_bp
    app.register_blueprint(user_bp)

    # 注册用户模块蓝图
    from .resources.news import news_bp
    app.register_blueprint(news_bp)

    return app

