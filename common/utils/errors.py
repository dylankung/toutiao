from flask import current_app, jsonify


def handle_redis_error(e):
    """
    处理redis异常
    """
    current_app.logger.error('[Redis] {}'.format(e))
    return jsonify(message='Unavailable service.'), 507


def handler_mysql_error(e):
    """
    处理mysql异常
    """
    current_app.logger.error('[MySQL] {}'.format(e))
    return jsonify(message='Unavailable service.'), 507
