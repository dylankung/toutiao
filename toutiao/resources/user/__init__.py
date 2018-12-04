from flask import Blueprint
from flask_restful import Api

from .views import passport, following, collection, liking, dislike, report
from utils.output import output_json

user_bp = Blueprint('user', __name__)
user_api = Api(user_bp, catch_all_404s=True)
user_api.representation('application/json')(output_json)

user_api.add_resource(passport.SMSVerificationCodeResource, '/v1_0/sms/codes/<mobile:mobile>',
                      endpoint='SMSVerificationCode')

user_api.add_resource(passport.AuthorizationResource, '/v1_0/authorizations',
                      endpoint='Authorization')

user_api.add_resource(following.FollowingListResource, '/v1_0/user/followings',
                      endpoint='Followings')

user_api.add_resource(following.FollowingResource, '/v1_0/user/followings/<int(min=1):target>',
                      endpoint='Following')

user_api.add_resource(collection.CollectionListResource, '/v1_0/user/collections',
                      endpoint='Collections')

user_api.add_resource(collection.CollectionResource, '/v1_0/user/collections/<int(min=1):target>',
                      endpoint='Collection')

user_api.add_resource(liking.LikingListResource, '/v1_0/user/likings',
                      endpoint='Likings')

user_api.add_resource(liking.LikingResource, '/v1_0/user/likings/<int(min=1):target>',
                      endpoint='Liking')

user_api.add_resource(dislike.DislikeListResource, '/v1_0/user/dislikes',
                      endpoint='Dislikes')

user_api.add_resource(dislike.DislikeResource, '/v1_0/user/dislikes/<int(min=1):target>',
                      endpoint='Dislike')

user_api.add_resource(report.ReportListResource, '/v1_0/user/reports',
                      endpoint='Reports')
