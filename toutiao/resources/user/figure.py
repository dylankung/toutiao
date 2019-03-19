from flask_restful import Resource
from flask import g

from utils.decorators import login_required, set_db_to_read
from cache import user as cache_user


class FigureResource(Resource):
    """
    用户统计数据
    """
    method_decorators = [set_db_to_read, login_required]

    def get(self):
        """
        获取用户统计数据
        """
        user = cache_user.UserProfileCache(g.user_id).get()

        return {'fans_count': user['fans_count'], 'read_count': user['read_count']}
