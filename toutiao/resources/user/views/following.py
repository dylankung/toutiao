from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.exc import IntegrityError
from flask import g

from utils.decorators import login_required
from models.user import Relation, User
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
            follow = Relation(user_id=g.user_id, target_user_id=target, relation=Relation.RELATION.FOLLOW)
            db.session.add(follow)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            ret = Relation.query.filter(Relation.user_id == g.user_id,
                                        Relation.target_user_id == target,
                                        Relation.relation != Relation.RELATION.FOLLOW)\
                .update({'relation': Relation.RELATION.FOLLOW})
        if ret > 0:
            # TODO 更新用户缓存
            User.query.filter_by(id=target).update({'fans_count': User.fans_count+1})
            User.query.filter_by(id=g.user_id).update({'following_count': User.following_count+1})
        db.session.commit()
        return {'target': target}, 201


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
        if ret > 0:
            # TODO 更新用户缓存
            User.query.filter_by(id=target).update({'fans_count': User.fans_count-1})
            User.query.filter_by(id=g.user_id).update({'following_count': User.following_count-1})
        db.session.commit()
        return {'message': 'OK'}, 204

