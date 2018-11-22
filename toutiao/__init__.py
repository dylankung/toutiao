import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

from flask import Flask
from logging.handlers import RotatingFileHandler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utils.logging import set_logging
from utils.converters import register_converters


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
    set_logging(app)

    # 注册url转换器
    register_converters(app)

    # 数据库连接初始化
    from models import db
    db.init_app(app)

    # 注册用户模块蓝图
    from .resources.user import user_bp
    app.register_blueprint(user_bp)

    # 注册新闻模块蓝图
    from .resources.news import news_bp
    app.register_blueprint(news_bp)

    return app
