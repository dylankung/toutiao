from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.exc import IntegrityError
from flask import g

from utils.decorators import login_required
from models.user import Relation, User
from utils import parser
from models import db
from cache import user as cache_user


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
            follow = Relation(user_id=g.user_id, target_user_id=target, relation=Relation.RELATION.FOLLOW)
            db.session.add(follow)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            ret = Relation.query.filter(Relation.user_id == g.user_id,
                                        Relation.target_user_id == target,
                                        Relation.relation != Relation.RELATION.FOLLOW)\
                .update({'relation': Relation.RELATION.FOLLOW})
            db.session.commit()
        if ret > 0:
            cache_user.update_user_following_count(g.user_id, target)
        return {'target': target}, 201

    def get(self):
        """
        获取关注的用户列表
        """
        pass


class FollowingResource(Resource):
    """
    关注用户
    """
    method_decorators = [login_required]

    def delete(self, target):
        """
        取消关注用户
        """
        ret = Relation.query.filter(Relation.user_id == g.user_id,
                                    Relation.target_user_id == target,
                                    Relation.relation == Relation.RELATION.FOLLOW)\
            .update({'relation': Relation.RELATION.DELETE})
        db.session.commit()

        if ret > 0:
            cache_user.update_user_following_count(g.user_id, target, -1)
        return {'message': 'OK'}, 204

