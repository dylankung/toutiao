from flask import Blueprint
from flask_restful import Api

from utils.errors import errors
from .views import passport


user_bp = Blueprint('user', __name__)
user_api = Api(user_bp, errors=errors)

user_api.add_resource(passport.SMSVerificationCode, '/v1_0/sms/codes/<mobile:mobile>')
# user_api.add_resource(passport.Authorization, '/v1_0/authorizations')

