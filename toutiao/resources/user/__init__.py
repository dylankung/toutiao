from flask import Blueprint
from flask_restful import Api

from .views import passport, follow
from utils.output import output_json

user_bp = Blueprint('user', __name__)
user_api = Api(user_bp, catch_all_404s=True)
user_api.representation('application/json')(output_json)

user_api.add_resource(passport.SMSVerificationCodeResource, '/v1_0/sms/codes/<mobile:mobile>',
                      endpoint='SMSVerificationCode')
user_api.add_resource(passport.AuthorizationResource, '/v1_0/authorizations',
                      endpoint='Authorization')
user_api.add_resource(follow.FollowingListResource, '/v1_0/user/followings',
                      endpoint='Followings')
user_api.add_resource(follow.FollowingResource, '/v1_0/user/following/<int:target>',
                      endpoint='Following')
