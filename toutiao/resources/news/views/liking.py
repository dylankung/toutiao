from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import g, current_app
from sqlalchemy.exc import IntegrityError
import time

from utils.decorators import login_required
from utils import parser
from models import db
from models.news import Attitude, ArticleStatistic, CommentLiking, Comment
from cache import comment as cache_comment
from cache import article as cache_article
from cache import user as cache_user


class ArticleLikingListResource(Resource):
    """
    文章点赞
    """
    method_decorators = [login_required]

    def post(self):
        """
        文章点赞
        """
        json_parser = RequestParser()
        json_parser.add_argument('target', type=parser.article_id, required=True, location='json')
        args = json_parser.parse_args()
        target = args.target

        # 此次操作前，用户对文章可能是没有态度，也可能是不喜欢，需要先查询对文章的原始态度，然后对相应的统计数据进行累计或减少
        # TODO 如果统计影响性能，可以改为定时

        atti = Attitude.query.filter_by(user_id=g.user_id, article_id=target).first()
        if atti is None:
            attitude = Attitude(user_id=g.user_id, article_id=target, attitude=Attitude.ATTITUDE.LIKING)
            db.session.add(attitude)
            # ArticleStatistic.query.filter_by(id=target).update({'like_count': ArticleStatistic.like_count + 1})
            cache_article.update_article_liking_count(target)
            db.session.commit()
        else:
            if atti.attitude == Attitude.ATTITUDE.DISLIKE:
                # 原先是不喜欢
                atti.attitude = Attitude.ATTITUDE.LIKING
                db.session.add(atti)
                ArticleStatistic.query.filter_by(id=target).update({
                    'dislike_count': ArticleStatistic.dislike_count - 1
                })
                cache_article.update_article_liking_count(target)
                db.session.commit()
            elif atti.attitude is None:
                # 存在数据，但是无态度
                atti.attitude = Attitude.ATTITUDE.LIKING
                db.session.add(atti)
                # ArticleStatistic.query.filter_by(id=target).update({
                #     'like_count': ArticleStatistic.like_count + 1,
                # })
                cache_article.update_article_liking_count(target)
                db.session.commit()

        # 发送点赞通知
        _user = cache_user.get_user(g.user_id)
        _article = cache_article.get_article_info(target)
        _data = {
            'user_id': g.user_id,
            'user_name': _user['name'],
            'user_photo': _user['photo'],
            'art_id': target,
            'art_title': _article['title'],
            'timestamp': int(time.time())
        }
        current_app.sio.emit('liking notify', data=_data, room=str(target))

        return {'target': target}, 201


class ArticleLikingResource(Resource):
    """
    文章点赞
    """
    method_decorators = [login_required]

    def delete(self, target):
        """
        取消文章点赞
        """
        ret = Attitude.query.filter_by(user_id=g.user_id, article_id=target, attitude=Attitude.ATTITUDE.LIKING) \
            .update({'attitude': None})
        if ret > 0:
            # ArticleStatistic.query.filter_by(id=target).update({'like_count': ArticleStatistic.like_count - 1})
            cache_article.update_article_liking_count(target, -1)
        db.session.commit()
        return {'message': 'OK'}, 204


class CommentLikingListResource(Resource):
    """
    评论点赞
    """
    method_decorators = [login_required]

    def post(self):
        """
        评论点赞
        """
        json_parser = RequestParser()
        json_parser.add_argument('target', type=parser.comment_id, required=True, location='json')
        args = json_parser.parse_args()
        target = args.target
        ret = 1
        try:
            comment_liking = CommentLiking(user_id=g.user_id, comment_id=target)
            db.session.add(comment_liking)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            ret = CommentLiking.query.filter_by(user_id=g.user_id, comment_id=target, is_deleted=True) \
                .update({'is_deleted': False})
        if ret > 0:
            Comment.query.filter_by(id=target).update({'like_count': Comment.like_count + 1})
            cache_comment.update_comment_liking_count(target)
        db.session.commit()
        return {'target': target}, 201


class CommentLikingResource(Resource):
    """
    评论点赞
    """
    method_decorators = [login_required]

    def delete(self, target):
        """
        取消对评论点赞
        """
        ret = CommentLiking.query.filter_by(user_id=g.user_id, comment_id=target, is_deleted=False) \
            .update({'is_deleted': True})
        if ret > 0:
            Comment.query.filter_by(id=target).update({'like_count': Comment.like_count - 1})
            cache_comment.update_comment_liking_count(target, -1)
        db.session.commit()
        return {'message': 'OK'}, 204
