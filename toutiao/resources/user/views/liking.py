from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import g

from utils.decorators import login_required
from utils import parser
from models import db
from models.news import Attitude, ArticleStatistic


class LikingListResource(Resource):
    """
    用户点赞
    """
    method_decorators = [login_required]

    def post(self):
        """
        用户点赞
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
            ArticleStatistic.query.filter_by(id=target).update({'like_count': ArticleStatistic.like_count + 1})
            db.session.commit()
        else:
            if atti.attitude == Attitude.ATTITUDE.DISLIKE:
                # 原先是不喜欢
                atti.attitude = Attitude.ATTITUDE.LIKING
                db.session.add(atti)
                ArticleStatistic.query.filter_by(id=target).update({
                    'like_count': ArticleStatistic.like_count + 1,
                    'dislike_count': ArticleStatistic.dislike_count - 1
                })
                db.session.commit()
            elif atti.attitude is None:
                # 存在数据，但是无态度
                atti.attitude = Attitude.ATTITUDE.LIKING
                db.session.add(atti)
                ArticleStatistic.query.filter_by(id=target).update({
                    'like_count': ArticleStatistic.like_count + 1,
                })
                db.session.commit()

        return {'target': target}


class LikingResource(Resource):
    """
    点赞
    """
    method_decorators = [login_required]

    def delete(self, target):
        """
        用户取消点赞
        """
        ret = Attitude.query.filter_by(user_id=g.user_id, article_id=target, attitude=Attitude.ATTITUDE.LIKING) \
            .update({'attitude': None})
        if ret > 0:
            ArticleStatistic.query.filter_by(id=target).update({'like_count': ArticleStatistic.like_count - 1})
        db.session.commit()
        return {'message': 'OK'}, 204


