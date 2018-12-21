import re
import base64
import imghdr
from datetime import datetime

from cache import comment as cache_comment
from cache import channel as cache_channel
from cache import article as cache_article
from cache import user as cache_user


def mobile(mobile_str):
    """
    检验手机号格式
    :param mobile_str: str 被检验字符串
    :return: mobile_str
    """
    if re.match(r'^1[3-9]\d{9}$', mobile_str):
        return mobile_str
    else:
        raise ValueError('{} is not a valid mobile'.format(mobile_str))


def regex(pattern):
    """
    正则检验
    :param pattern: str 正则表达式
    :return:  检验函数
    """
    def validate(value_str):
        """
        检验字符串格式
        :param value_str: str 被检验字符串
        :return: bool 检验是否通过
        """
        if re.match(pattern, value_str):
            return value_str
        else:
            raise ValueError('Invalid params.')

    return validate


def user_id(value):
    """
    检查是否是user_id
    :param value: 被检验的值
    :return: user_id
    """
    try:
        _user_id = int(value)
    except Exception:
        raise ValueError('Invalid target user id.')
    else:
        if _user_id <= 0:
            raise ValueError('Invalid target user id.')
        else:
            ret = cache_user.determine_user_exists(_user_id)
            if ret:
                return _user_id
            else:
                raise ValueError('Invalid target user id.')


def article_id(value):
    """
    检查是否是article_id
    :param value: 被检验的值
    :return: article_id
    """
    try:
        _article_id = int(value)
    except Exception:
        raise ValueError('Invalid target article id.')
    else:
        if _article_id <= 0:
            raise ValueError('Invalid target article id.')
        else:
            ret = cache_article.determine_article_exists(_article_id)
            if ret:
                return _article_id
            else:
                raise ValueError('Invalid target article id.')


def comment_id(value):
    """
    检查是否是评论id
    :param value: 被检验的值
    :return: comment_id
    """
    try:
        _comment_id = int(value)
    except Exception:
        raise ValueError('Invalid target comment id.')
    else:
        if _comment_id <= 0:
            raise ValueError('Invalid target comment id.')
        else:
            ret = cache_comment.determine_comment_exists(_comment_id)
            if ret:
                return _comment_id
            else:
                raise ValueError('Invalid target comment id.')


def channel_id(value):
    """
    检查是否是频道id
    :param value: 被检验的值
    :return: channel_id
    """
    try:
        _channel_id = int(value)
    except Exception:
        raise ValueError('Invalid channel id.')
    else:
        if _channel_id <= 0:
            raise ValueError('Invalid channel id.')
        else:
            ret = cache_channel.determine_channel_exists(_channel_id)
            if ret:
                return _channel_id
            else:
                raise ValueError('Invalid channel id.')


def date(value):
    """
    检查是否是合法日期
    :param value: 被检验的值
    :return: date
    """
    try:
        _date = datetime.strptime(value, '%Y-%m-%d')
    except Exception:
        raise ValueError('Invalid date param.')
    else:
        return _date


def image(value):
    """
    检查是否是图片文件
    :param value:
    :return:
    """
    try:
        photo = base64.b64decode(value)
        file_header = photo[:32]
        file_type = imghdr.what(None, file_header)
    except Exception:
        raise ValueError('Invalid image.')
    else:
        if not file_type:
            raise ValueError('Invalid image.')
        else:
            return photo


def id_number(value):
    id_number_pattern = r'(^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$)|(^[1-9]\d{5}\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{2}$)'
    if re.match(id_number_pattern, value):
        return value.upper()
    else:
        raise ValueError('Invalid id number.')
