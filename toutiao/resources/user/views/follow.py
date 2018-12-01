from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.dialects.mysql import insert
from flask import g

from utils.decorators import login_required
from models.user import Follow
from utils import parser
from models import db


class FollowingListResource(Resource):
    """
    关注用户
    """
    method_decorators = [login_required]

    def post(self):
        """
        关注用户
        """
        json_parser = RequestParser()
        json_parser.add_argument('target', type=parser.user_id, required=True, location='json')
        args = json_parser.parse_args()
        target = args.target
        if target == g.user_id:
            return {'message': 'User cannot follow self.'}, 400
        query = insert(Follow).values(user_id=g.user_id, following_user_id=target, is_deleted=False)
        query = query.on_duplicate_key_update(is_deleted=False)
        db.session.execute(query)
        db.session.commit()
        return {'target': target}


class FollowingResource(Resource):
    """
    关注用户
    """
    method_decorators = [login_required]

    def delete(self, target):
        """
        取消关注用户
        """
        Follow.query.filter_by(user_id=g.user_id, following_user_id=target).update({'is_deleted': True})
        db.session.commit()
        return {'message': 'OK'}, 204

