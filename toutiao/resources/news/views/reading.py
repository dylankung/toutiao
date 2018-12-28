from flask_restful import Resource
from flask import g
from flask_restful import inputs
from flask_restful.reqparse import RequestParser
from sqlalchemy import func
from sqlalchemy.orm import load_only

from utils.decorators import login_required
from .. import constants
from cache import user as cache_user
from cache import article as cache_article
from models.news import Read
from models import db
from utils.logging import write_trace_log


class ReadingHistoryListResource(Resource):
    """
    用户阅读历史
    """
    method_decorators = [login_required]

    def get(self):
        """
        获取用户阅读历史
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

        user_id = g.user_id
        cache_user.synchronize_reading_history_to_db(user_id)

        # TODO 未做缓存
        ret = db.session.query(func.count(Read.id)).filter_by(user_id=g.user_id).first()
        total_count = ret[0]
        results = []
        if total_count > 0 and (page - 1) * per_page < total_count:
            reads = Read.query.options(load_only(Read.article_id)) \
                .filter_by(user_id=g.user_id) \
                .order_by(Read.utime.desc()).offset((page - 1) * per_page).limit(per_page).all()
            for read in reads:
                article = cache_article.get_article_info(read.article_id)
                results.append(article)

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}


class ReadingDurationResource(Resource):
    """
    阅读时长
    """
    def post(self):
        req_parser = RequestParser()
        req_parser.add_argument('Trace', type=inputs.regex(r'^.+$'), required=True, location='headers')
        req_parser.add_argument('duration', type=inputs.natural, required=True, location='json')
        args = req_parser.parse_args()

        write_trace_log(args.Trace, args.duration)

        return {'message': 'OK'}, 201