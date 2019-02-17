from flask_restful import Resource
from flask import g
from flask_restful.reqparse import RequestParser
from flask_restful import inputs
from sqlalchemy.orm import load_only, join, contains_eager
from sqlalchemy import func

from utils.decorators import verify_required
from models.news import Article, ArticleStatistic
from . import constants
from models import db


class ArticleListResource(Resource):
    """
    评论
    """
    method_decorators = [verify_required]

    def get(self):
        """
        获取评论文章
        """
        req_parser = RequestParser()
        req_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        req_parser.add_argument('per_page', type=inputs.int_range(1,
                                                                  constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                                  'per_page'),
                                required=False, location='args')
        args = req_parser.parse_args()
        page = 1 if args['page'] is None else args['page']
        per_page = args.per_page if args.per_page else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

        ret = db.session.query(func.count(Article.id)).filter(Article.user_id == g.user_id,
                                                              Article.status == Article.STATUS.APPROVED).first()
        total_count = ret[0]
        results = []

        if total_count > 0:

            articles = Article.query.join(Article.statistic).options(
                load_only(Article.id, Article.title, Article.allow_comment, Article.comment_count),
                contains_eager(Article.statistic).load_only(ArticleStatistic.fans_comment_count)
            ).filter(Article.user_id == g.user_id, Article.status == Article.STATUS.APPROVED)\
                .order_by(Article.id.desc()).offset((page-1)*per_page).limit(per_page).first()

            for article in articles:
                results.append(dict(
                    id=article.id,
                    title=article.title,
                    allow_comment=article.allow_comment,
                    comment_count=article.comment_count,
                    fans_comment_count=article.statistic.fans_comment_count
                ))

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}
