from flask import Blueprint
from flask_restful import Api

from .views import passport
from utils.errors import errors


user_bp = Blueprint('user', __name__)
user_api = Api(user_bp, errors=errors)

user_api.add_resource(passport.SMSVerificationCode, '/v1_0/sms/codes/<mobile:mobile>')

