from flask_restful import Resource
from flask_limiter.util import get_remote_address
from flask import request
import random

from toutiao import limiter
from .. import constants


class SMSVerificationCode(Resource):
    """
    短信验证码
    """
    error_message = 'Too many requests.'

    decorators = [
        limiter.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_MOBILE,
                      key_func=lambda: request.view_args['mobile'],
                      error_message=error_message),
        limiter.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
                      key_func=get_remote_address,
                      error_message=error_message)
    ]

    def get(self, mobile):
        code = '{:0>6d}'.format(random.randint(0, 999999))

