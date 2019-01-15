from flask_restful import Resource
from flask_limiter.util import get_remote_address
from flask import request, current_app, g
from flask_restful.reqparse import RequestParser
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import load_only

from celery_tasks.sms.tasks import send_verification_code
from utils import parser
from models.user import User, UserProfile
from utils.jwt_util import generate_jwt
from cache.user import save_user_data_cache
from utils.gt3.geetest import GeetestLib
from . import constants


class CaptchaResource(Resource):
    """
    验证码
    """
    def get(self, mobile):
        """
        获取验证码
        """
        r = current_app.redis_cli['sms_code']
        gt = GeetestLib(current_app.config['GEETEST_ID'], current_app.config['GEETEST_KEY'])
        status = gt.pre_process(mobile)
        r.setex('capt:{}'.format(mobile), constants.GEETEST_EXPIRES, status)
        response_str = gt.get_response_str()
        return response_str


class SMSVerificationCodeResource(Resource):
    """
    短信验证码
    """
    # error_message = 'Too many requests.'
    #
    # decorators = [
    #     limiter.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_MOBILE,
    #                   key_func=lambda: request.view_args['mobile'],
    #                   error_message=error_message),
    #     limiter.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
    #                   key_func=get_remote_address,
    #                   error_message=error_message)
    # ]

    def get(self, mobile):
        req_paser = RequestParser()
        req_paser.add_argument('challenge', required=True, location='args')
        req_paser.add_argument('validate', required=True, location='args')
        req_paser.add_argument('seccode', required=True, location='args')
        args = req_paser.parse_args()
        challenge = args['challenge']
        validate = args['validate']
        seccode = args['seccode']

        r = current_app.redis_cli['sms_code']
        status = r.get('capt:{}'.format(mobile))
        if status is None:
            return {'message': 'Captcha expired.'}, 400
        status = int(status)

        gt = GeetestLib(current_app.config['GEETEST_ID'], current_app.config['GEETEST_KEY'])

        if status:
            success = gt.success_validate(challenge, validate, seccode, mobile, data='', userinfo='')
        else:
            success = gt.failback_validate(challenge, validate, seccode)

        if success:
            code = '{:0>6d}'.format(random.randint(0, 999999))
            r.setex('mp:code:{}'.format(mobile), constants.SMS_VERIFICATION_CODE_EXPIRES, code)
            send_verification_code.delay(mobile, code)
            return {'mobile': mobile}
        else:
            return {'message': 'Captcha validate failed.'}, 403


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
        req_parser = RequestParser()
        req_parser.add_argument('mobile', type=parser.mobile, required=True, location='json')
        req_parser.add_argument('code', type=parser.regex(r'^\d{6}$'), required=True, location='json')
        args = req_parser.parse_args()
        mobile = args.mobile
        code = args.code

        # 从redis中获取验证码
        real_code = current_app.redis_cli['sms_code'].get('mp:code:{}'.format(mobile))
        if not real_code or real_code.decode() != code:
            return {'message': 'Invalid code.'}, 400

        # 查询或保存用户
        user = User.query.options(load_only(User.id, User.name, User.profile_photo)).filter_by(mobile=mobile, is_verified=True).first()
        if user is None:
            return {'message': 'Please verify your real information in app.'}, 403

        token, refresh_token = self._generate_tokens(user.id)

        # 缓存用户信息
        save_user_data_cache(user.id)

        return {'token': token,
                'refresh_token': refresh_token,
                'id': user.id,
                'name': user.name,
                'photo': current_app.config['QINIU_DOMAIN'] + user.profile_photo}, 201

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









