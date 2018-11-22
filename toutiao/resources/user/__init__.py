from flask import Blueprint
from flask_restful import Api

from .views import passport

user_bp = Blueprint('user', __name__)
user_api = Api(user_bp)

user_api.add_resource(passport.SMSVerificationCode, '/v1_0/sms/codes/<mobile:mobile>')

