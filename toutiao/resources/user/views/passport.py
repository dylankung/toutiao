from flask_restful import Resource
from flask_limiter.util import get_remote_address
from flask import request
from flask_restful.reqparse import RequestParser
import random
from datetime import datetime
from sqlalchemy.orm import load_only

from toutiao.main import limiter, redis_cli
from celery_tasks.sms.tasks import send_verification_code
from .. import constants
from utils import parser
from models import db
from models.user import User, UserProfile
from utils.jwt_util import generate_jwt
from cache.user import save_user_data_cache


class SMSVerificationCodeResource(Resource):
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
        redis_cli['sms_code'].setex('code:{}'.format(mobile), constants.SMS_VERIFICATION_CODE_EXPIRES, code)
        send_verification_code.delay(mobile, code)
        return {'mobile': mobile}


class AuthorizationResource(Resource):
    """
    认证
    """
    def post(self):
        json_parser = RequestParser()
        json_parser.add_argument('mobile', type=parser.mobile, required=True, location='json')
        json_parser.add_argument('code', type=parser.regex(r'^\d{6}$'), required=True, location='json')
        args = json_parser.parse_args()
        mobile = args.mobile
        code = args.code

        # 从redis中获取验证码
        real_code = redis_cli['sms_code'].get('code:{}'.format(mobile))
        if not real_code or real_code.decode() != code:
            return {'message': 'Invalid code.'}, 400

        # 查询或保存用户
        user = User.query.options(load_only(User.id)).filter_by(mobile=mobile).first()
        if user is None:
            # 用户不存在，注册用户
            user = User(mobile=mobile, name=mobile, last_login=datetime.now())
            db.session.add(user)
            db.session.commit()
            profile = UserProfile(id=user.id)
            db.session.add(profile)
            db.session.commit()

        # 颁发JWT
        token = generate_jwt({'user_id': user.id})

        # 缓存用户信息
        save_user_data_cache(user.id, user)

        return {'token': token}, 201











