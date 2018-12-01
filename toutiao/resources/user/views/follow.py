from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import IntegrityError
from flask import g

from utils.decorators import login_required
from models.user import Follow, User
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
        ret = 1
        try:
            follow = Follow(user_id=g.user_id, following_user_id=target)
            db.session.add(follow)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            ret = Follow.query.filter_by(user_id=g.user_id, following_user_id=target, is_deleted=True)\
                .update({'is_deleted': False})
        if ret > 0:
            User.query.filter_by(id=target).update({'fans_count': User.fans_count+1})
            User.query.filter_by(id=g.user_id).update({'following_count': User.following_count+1})
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
        ret = Follow.query.filter_by(user_id=g.user_id, following_user_id=target, is_deleted=False)\
            .update({'is_deleted': True})
        if ret > 0:
            User.query.filter_by(id=target).update({'fans_count': User.fans_count-1})
            User.query.filter_by(id=g.user_id).update({'following_count': User.following_count-1})
        db.session.commit()
        return {'message': 'OK'}, 204

