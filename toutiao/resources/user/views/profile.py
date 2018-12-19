from flask_restful import Resource
from flask import g
from sqlalchemy.orm import load_only

from utils.decorators import login_required
from cache import user as cache_user
from models.user import Relation


class UserResource(Resource):
    """
    用户数据资源
    """
    def get(self, target):
        """
        获取target用户的数据
        :param target: 目标用户id
        """
        exist = cache_user.determine_user_exists(target)
        if not exist:
            return {'message': 'Invalid target user.'}, 400

        user_data = cache_user.get_user(target)

        user_data['is_following'] = False
        if g.user_id:
            # Check if user has followed target user.
            ret = Relation.query.options(load_only(Relation.id))\
                .filter_by(user_id=g.user_id, target_user_id=target, relation=Relation.RELATION.FOLLOW).first()
            if ret:
                user_data['is_following'] = True
        user_data['id'] = target
        return user_data


class UserSelfResource(Resource):
    """
    用户自己的数据
    """
    method_decorators = [login_required]

    def get(self):
        """
        获取当前用户自己的数据
        """
        user_data = cache_user.get_user(g.user_id)
        user_data['id'] = g.user_id
        return user_data
