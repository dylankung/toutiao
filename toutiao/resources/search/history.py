from flask_restful import Resource
from flask import g
from sqlalchemy.orm import load_only

from utils.decorators import login_required
from models.user import Search
from . import constants
from models import db


class HistoryListResource(Resource):
    """
    搜索历史
    """
    method_decorators = [login_required]

    def get(self):
        """
        获取用户搜索历史
        """
        ret = Search.query.options(load_only(Search.keyword)).filter_by(user_id=g.user_id, is_deleted=False)\
            .order_by(Search.utime.desc()).limit(constants.USER_SEARCH_HISTORY_RETRIEVE_LIMIT).all()

        return {'keywords': [search.keyword for search in ret]}

    def delete(self):
        """
        删除搜索历史
        """
        Search.query.filter_by(user_id=g.user_id, is_deleted=False).update({'is_deleted': True})
        db.session.commit()
        return {'message': 'OK'}, 204
