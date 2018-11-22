from flask import request
from logging import Formatter
from logging.config import dictConfig
import os


class RequestFormatter(Formatter):
    """
    针对请求信息的日志格式
    """
    def format(self, record):
        record.url = request.url
        record.remote_addr = request.remote_addr
        return super().format(record)


def set_logging(app):
    """
    设置日志
    :param app: Flask app对象
    :return:
    """
    dictConfig({
        'version': 1,
        'formatters': {
            'access_format': {
                'format': '%(message)s'
            },
            'console_format': {
                'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
            },
            'flask_format': {
                'class': 'utils.logging.RequestFormatter',
                'format': '[%(asctime)s] %(remote_addr)s requested %(url)s\n'
                          '%(levelname)s in %(module)s %(lineno)d: %(message)s'
            },
            'sms_format': {
                'format': '%(levelname)s %(asctime)s %(message)s'
            },
        },
        'handlers': {
            'access_console': {
                'class': 'logging.StreamHandler',
                'formatter': 'access_format'
            },
            'access_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(app.config['LOGGING_FILE_DIR'], 'access.log'),
                'maxBytes': app.config['LOGGING_FILE_MAX_BYTES'],
                'backupCount': app.config['LOGGING_FILE_BACKUP'],
                'formatter': 'access_format'
            },
            'flask_console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console_format'
            },
            'flask_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(app.config['LOGGING_FILE_DIR'], 'flask.log'),
                'maxBytes': app.config['LOGGING_FILE_MAX_BYTES'],
                'backupCount': app.config['LOGGING_FILE_BACKUP'],
                'formatter': 'flask_format'
            },
            'sms_console': {
                'class': 'logging.StreamHandler',
                'formatter': 'sms_format'
            },
            'limit_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(app.config['LOGGING_FILE_DIR'], 'limit.log'),
                'maxBytes': app.config['LOGGING_FILE_MAX_BYTES'],
                'backupCount': app.config['LOGGING_FILE_BACKUP'],
                'formatter': 'flask_format'
            }
        },
        'loggers': {
            'werkzeug': {
                'handlers': ['access_console', 'access_file'],
                'level': app.config['LOGGING_LEVEL']
            },
            'flask.app': {
                'handlers': ['flask_console', 'flask_file'],
                'level': app.config['LOGGING_LEVEL']
            },
            'flask.sms': {
                'handlers': ['sms_console'],
                'level': app.config['LOGGING_LEVEL']
            },
            'flask-limiter': {
                'handlers': ['flask_console', 'limit_file'],
                'levle': app.config['LOGGING_LEVEL']
            }
        }
    })
