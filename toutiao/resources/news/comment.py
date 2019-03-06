from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask_restful.inputs import positive, int_range
from flask import g, current_app
from sqlalchemy.orm import load_only
import time

from utils.decorators import login_required
from utils import parser
from models import db
from models.news import Comment, Article
from cache import comment as cache_comment
from cache import article as cache_article
from cache import user as cache_user
from . import constants


class CommentListResource(Resource):
    """
    评论
    """
    method_decorators = {'post': [login_required]}

    def post(self):
        """
        创建评论
        """
        json_parser = RequestParser()
        json_parser.add_argument('target', type=positive, required=True, location='json')
        json_parser.add_argument('content', required=True, location='json')
        json_parser.add_argument('art_id', type=parser.article_id, required=False, location='json')

        args = json_parser.parse_args()
        target = args.target
        content = args.content
        article_id = args.art_id

        if not content:
            return {'message': 'Empty content.'}, 400

        # TODO 缓存中增加是否允许评论
        article = Article.query.options(Article.allow_comment).filter_by(id=article_id).first()
        if not article.allow_comment:
            return {'message': 'Article denied comment.'}, 403

        if not article_id:
            # 对文章评论
            article_id = target

            comment = Comment(user_id=g.user_id, article_id=article_id, parent_id=None, content=content)
            db.session.add(comment)
            db.session.commit()
            # TODO 增加评论审核后 在评论审核中累计评论数量
            cache_article.update_article_comment_count(article_id)
            cache_comment.update_comment_by_article(article_id, comment)

            # 发送评论通知
            _user = cache_user.get_user(g.user_id)
            _article = cache_article.get_article_info(article_id)
            _data = {
                'user_id': g.user_id,
                'user_name': _user['name'],
                'user_photo': _user['photo'],
                'art_id': article_id,
                'art_title': _article['title'],
                'timestamp': int(time.time())
            }
            current_app.sio.emit('comment notify', data=_data, room=str(_article['aut_id']))

        else:
            # 对评论的回复
            ret = Comment.query.options(load_only(Comment.id)).filter_by(id=target, article_id=article_id).first()
            if ret is None:
                return {'message': 'Invalid target comment id.'}, 400

            comment = Comment(user_id=g.user_id, article_id=article_id, parent_id=target, content=content)
            db.session.add(comment)
            db.session.commit()

            # TODO 增加评论审核后 在评论审核中累计评论数量
            cache_article.update_article_comment_count(article_id)
            cache_comment.update_comment_reply_count(target)
            cache_comment.update_reply_by_comment(target, comment)

        return {'com_id': comment.id, 'target': target, 'art_id': article_id}, 201

        # TODO 评论审核时更新评论缓存数据

    def _comment_type(self, value):
        """
        检查评论类型参数
        """
        if value in ('a', 'c'):
            return value
        else:
            raise ValueError('Invalid type param.')

    def get(self):
        """
        获取评论列表
        """
        # /comments?type,source,offset,limit
        # return = {
        #     'results': [
        #         {
        #             'com_id': 0,
        #             'aut_id': 0,
        #             'aut_name': '',
        #             'aut_photo': '',
        #             'like_count': 0,
        #             'reply_count': 0,
        #             'pubdate': '',
        #             'content': ''
        #         }
        #     ],
        #     'total_count': 0,
        #     'last_id': 0,
        #     'end_id': 0,
        # }
        qs_parser = RequestParser()
        qs_parser.add_argument('type', type=self._comment_type, required=True, location='args')
        qs_parser.add_argument('source', type=positive, required=True, location='args')
        qs_parser.add_argument('offset', type=positive, required=False, location='args')
        qs_parser.add_argument('limit', type=int_range(constants.DEFAULT_COMMENT_PER_PAGE_MIN,
                                                       constants.DEFAULT_COMMENT_PER_PAGE_MAX,
                                                       argument='limit'), required=False, location='args')
        args = qs_parser.parse_args()
        limit = args.limit if args.limit is not None else constants.DEFAULT_COMMENT_PER_PAGE_MIN

        if args.type == 'a':
            # 文章评论
            article_id = args.source

            result = cache_comment.get_comments_by_article(article_id, args.offset, limit)
        else:
            # 评论的评论
            comment_id = args.source

            result = cache_comment.get_reply_by_comment(comment_id, args.offset, limit)

        return result

