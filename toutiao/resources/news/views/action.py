from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.exc import IntegrityError
from flask import g

from utils.decorators import login_required
from utils import parser
from models import db
from models.news import Collection, ArticleStatistic


class CollectionListResource(Resource):
    """
    文章收藏
    """
    method_decorators = [login_required]

    def post(self):
        """
        用户收藏文章
        """
        json_parser = RequestParser()
        json_parser.add_argument('target', type=parser.article_id, required=True, location='json')
        args = json_parser.parse_args()
        target = args.target
        ret = 1
        try:
            collection = Collection(user_id=g.user_id, article_id=target)
            db.session.add(collection)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            ret = Collection.query.filter_by(user_id=g.user_id, article_id=target, is_deleted=True) \
                .update({'is_deleted': False})
        if ret > 0:
            ArticleStatistic.query.filter_by(id=target).update({'collect_count': ArticleStatistic.collect_count + 1})
        db.session.commit()
        return {'target': target}


class CollectionResource(Resource):
    """
    文章收藏
    """
    method_decorators = [login_required]

    def delete(self, target):
        """
        用户取消收藏
        """
        ret = Collection.query.filter_by(user_id=g.user_id, article_id=target, is_deleted=False) \
            .update({'is_deleted': True})
        if ret > 0:
            ArticleStatistic.query.filter_by(id=target).update({'collect_count': ArticleStatistic.collect_count - 1})
        db.session.commit()
        return {'message': 'OK'}, 204
