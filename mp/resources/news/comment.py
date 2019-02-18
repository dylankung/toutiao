from flask_restful import Resource
from flask import g
from flask_restful.reqparse import RequestParser
from flask_restful import inputs

from utils.decorators import verify_required
from models.news import Article
from models import db


class CommentStatusResource(Resource):
    """
    评论状态
    """
    method_decorators = [verify_required]

    def put(self):
        """
        修改评论状态
        """
        req_parser = RequestParser()
        req_parser.add_argument('article_id', type=inputs.positive, required=True, location='args')
        req_parser.add_argument('allow_comment', type=inputs.boolean, required=True, location='json')
        args = req_parser.parse_args()

        ret = Article.query.filter_by(id=args.article_id, user_id=g.user_id, status=Article.STATUS.APPROVED)\
            .update({'allow_comment': args.allow_comment})
        db.session.commit()

        if ret > 0:
            return {'article_id': args.article_id, 'allow_comment': args.allow_comment}, 201
        else:
            return {'message': 'Invalid article status.'}, 400


