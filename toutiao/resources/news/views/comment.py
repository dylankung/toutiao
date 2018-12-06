from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask_restful.inputs import positive
from flask import g
from sqlalchemy.orm import load_only

from utils.decorators import login_required
from utils import parser
from models import db
from models.news import Comment, Article


class CommentListResource(Resource):
    """
    评论
    """
    method_decorators = [login_required]

    def post(self):
        """
        创建评论
        """
        json_parser = RequestParser()
        json_parser.add_argument('target', type=positive, required=True, location='json')
        json_parser.add_argument('content', required=True, location='json')
        json_parser.add_argument('aid', type=parser.article_id, required=False, location='json')

        args = json_parser.parse_args()
        target = args.target
        content = args.content
        article_id = args.aid

        if not article_id:
            # 对文章评论
            article_id = target

            comment = Comment(user_id=g.user_id, article_id=article_id, parent_id=None, content=content)
            db.session.add(comment)
            # TODO 增加评论审核后 在评论审核中累计评论数量
            Article.query.filter_by(id=article_id).update({'comment_count': Article.comment_count + 1})
            db.session.commit()
        else:
            # 对评论的子评论
            ret = Comment.query.options(load_only(Comment.id)).filter_by(id=target, article_id=article_id).first()
            if ret is None:
                return {'message': 'Invalid target comment id.'}, 400

            comment = Comment(user_id=g.user_id, article_id=article_id, parent_id=target, content=content)
            db.session.add(comment)
            # TODO 增加评论审核后 在评论审核中累计评论数量
            Article.query.filter_by(id=article_id).update({'comment_count': Article.comment_count + 1})
            db.session.commit()

        return {'cid': comment.id, 'target': target, 'aid': article_id}, 201


    def get(self):
        """
        获取评论列表
        """
        pass