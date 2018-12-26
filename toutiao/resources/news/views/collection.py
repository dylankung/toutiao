from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.exc import IntegrityError
from flask import g
from sqlalchemy.orm import load_only
from flask_restful import inputs
from sqlalchemy import func

from utils.decorators import login_required
from utils import parser
from models import db
from models.news import Collection
from .. import constants
from cache import article as cache_article
from utils.logging import write_trace_log


class CollectionListResource(Resource):
    """
    文章收藏
    """
    method_decorators = [login_required]

    def post(self):
        """
        用户收藏文章
        """
        req_parser = RequestParser()
        req_parser.add_argument('target', type=parser.article_id, required=True, location='json')
        req_parser.add_argument('trace', type=inputs.regex(r'^.+$'), required=False, location='args')
        args = req_parser.parse_args()

        # 记录埋点日志
        if args.trace:
            write_trace_log(args.trace)

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
            # ArticleStatistic.query.filter_by(id=target).update({'collect_count': ArticleStatistic.collect_count + 1})
            cache_article.update_article_collect_count(target)
        db.session.commit()
        return {'target': target}, 201

    def get(self):
        """
        获取用户的收藏历史
        """
        qs_parser = RequestParser()
        qs_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        qs_parser.add_argument('per_page', type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                                 constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                                 'per_page'),
                               required=False, location='args')
        args = qs_parser.parse_args()
        page = 1 if args.page is None else args.page
        per_page = args.per_page if args.per_page else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

        # TODO 未做缓存
        ret = db.session.query(func.count(Collection.id)).filter_by(user_id=g.user_id, is_deleted=False).first()
        total_count = ret[0]
        results = []
        if total_count > 0 and (page-1) * per_page < total_count:
            collections = Collection.query.options(load_only(Collection.article_id))\
                .filter_by(user_id=g.user_id, is_deleted=False)\
                .order_by(Collection.utime.desc()).offset((page-1)*per_page).limit(per_page).all()
            for collection in collections:
                article = cache_article.get_article_info(collection.article_id)
                results.append(article)

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}


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
            # ArticleStatistic.query.filter_by(id=target).update({'collect_count': ArticleStatistic.collect_count - 1})
            cache_article.update_article_collect_count(target, -1)
        db.session.commit()
        return {'message': 'OK'}, 204


