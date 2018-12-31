import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
import grpc
from elasticsearch5 import Elasticsearch

from . import create_app
from settings.default import DefaultConfig
from utils.logging import create_logger
from utils.converters import register_converters
from utils.errors import handle_redis_error, handler_mysql_error
from utils.middlewares import jwt_authentication
from utils.redis_client import create_redis_clients


app = create_app(DefaultConfig, enable_config_file=True)

# 限流器
limiter = Limiter(app, key_func=get_remote_address)

# 配置日志
create_logger(app)

# 注册url转换器
register_converters(app)

# redis
redis_cli = create_redis_clients(app)
app.redis_cli = redis_cli

# rpc
rpc_reco = grpc.insecure_channel(app.config['RPC'].RECOMMEND)

# Elasticsearch
es = Elasticsearch(
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
app.register_error_handler(RedisError, handle_redis_error)
app.register_error_handler(SQLAlchemyError, handler_mysql_error)

# 添加请求钩子
app.before_request(jwt_authentication)

# 注册用户模块蓝图
from .resources.user import user_bp
app.register_blueprint(user_bp)

# 注册新闻模块蓝图
from .resources.news import news_bp
app.register_blueprint(news_bp)

# 注册通知模块
from .resources.notice import notice_bp
app.register_blueprint(notice_bp)

# 搜索
from .resources.search import search_bp
app.register_blueprint(search_bp)


@app.route('/')
def route_map():
    """
    主视图，返回所有视图网址
    """
    rules_iterator = app.url_map.iter_rules()
    return jsonify({rule.endpoint: rule.rule for rule in rules_iterator if rule.endpoint not in ('route_map', 'static')})
