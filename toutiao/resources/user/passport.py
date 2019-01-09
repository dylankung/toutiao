from flask_restful import Resource
from flask_limiter.util import get_remote_address
from flask import request, current_app, g
from flask_restful.reqparse import RequestParser
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import load_only

from celery_tasks.sms.tasks import send_verification_code
from . import constants
from utils import parser
from models import db
from models.user import User, UserProfile
from utils.jwt_util import generate_jwt
from cache.user import save_user_data_cache
from toutiao import limiter


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
        current_app.redis_cli['sms_code'].setex('app:code:{}'.format(mobile), constants.SMS_VERIFICATION_CODE_EXPIRES, code)
        send_verification_code.delay(mobile, code)
        return {'mobile': mobile}


class AuthorizationResource(Resource):
    """
    认证
    """

    def _generate_tokens(self, user_id, with_refresh_token=True):
        """
        生成token 和refresh_token
        :param user_id: 用户id
        :return: token, refresh_token
        """
        # 颁发JWT
        now = datetime.utcnow()
        expiry = now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS'])
        # expiry = now + timedelta(minutes=current_app.config['JWT_EXPIRY_HOURS'])
        token = generate_jwt({'user_id': user_id, 'refresh': False}, expiry)
        refresh_token = None
        if with_refresh_token:
            refresh_expiry = now + timedelta(days=current_app.config['JWT_REFRESH_DAYS'])
            refresh_token = generate_jwt({'user_id': user_id, 'refresh': True}, refresh_expiry)
        return token, refresh_token

    def post(self):
        """
        登录创建token
        """
        json_parser = RequestParser()
        json_parser.add_argument('mobile', type=parser.mobile, required=True, location='json')
        json_parser.add_argument('code', type=parser.regex(r'^\d{6}$'), required=True, location='json')
        args = json_parser.parse_args()
        mobile = args.mobile
        code = args.code

        # 从redis中获取验证码
        real_code = current_app.redis_cli['sms_code'].get('app:code:{}'.format(mobile))
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

        token, refresh_token = self._generate_tokens(user.id)

        # 缓存用户信息
        save_user_data_cache(user.id, user)

        return {'token': token, 'refresh_token': refresh_token}, 201

    def put(self):
        """
        刷新token
        """
        user_id = g.user_id
        if user_id and g.refresh_token:

            token, refresh_token = self._generate_tokens(user_id, with_refresh_token=False)

            return {'token': token}, 201

        else:

            return {'message': 'Wrong refresh token.'}, 403










