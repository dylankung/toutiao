from flask_restful import Resource, abort
from flask_restful import marshal, fields
from flask import g, current_app
from sqlalchemy.orm import load_only
import pickle
from redis.exceptions import RedisError
import time

from models.news import Article
from models.user import User, Follow
from toutiao import redis_cli, rpc_cli
from rpc import article_reco_pb2_grpc
from rpc import article_reco_pb2
from .. import constants


class ArticleResource(Resource):
    """
    文章
    """
    def get(self, article_id):
        """
        获取文章详情
        :param article_id: int 文章id
        """
        user_id = g.user_id

        # 查询文章数据
        r_cache = redis_cli['cache']
        article_bytes = r_cache.get('A_{}'.format(article_id))
        if article_bytes:
            # 使用缓存
            article_dict = pickle.loads(article_bytes)
        else:
            # 查询数据库
            article = Article.query.options(load_only(
                Article.id,
                Article.user_id,
                Article.title,
                Article.is_advertising,
                Article.ctime
            )).filter_by(id=article_id, status=Article.STATUS.APPROVED).first()
            if article is None:
                abort(404, message='Article {} does not exist.'.format(article_id))

            article.user = User.query.options(load_only(
                User.id,
                User.name,
                User.profile_photo
            )).filter_by(id=article.user_id).first()

            article_fields = {
                'art_id': fields.Integer(attribute='id'),
                'title': fields.String(attribute='title'),
                'pubdate': fields.DateTime(attribute='ctime', dt_format='iso8601'),
                'content': fields.String(attribute='content.content'),
                'aut_id': fields.Integer(attribute='user_id'),
                'aut_name': fields.String(attribute='user.name'),
                'aut_photo': fields.String(attribute='user.profile_photo'),
            }
            article_dict = marshal(article, article_fields)

            # 缓存
            article_cache = pickle.dumps(article_dict)
            try:
                r_cache.setex('A_{}'.format(article_id), constants.CACHE_ARTICLE_EXPIRE, article_cache)
            except RedisError:
                pass

        # 非匿名用户添加用户的阅读历史
        if user_id:
            r_his = redis_cli['READING_HISTORY']
            r_his.hset('H_{}'.format(user_id), article_id, int(time.time()))

        # 查询关注
        article_dict['is_followed'] = False
        if user_id:
            ret = Follow.query.filter_by(user_id=user_id, following_user_id=article_dict['aut_id'], is_deleted=False).count()
            if ret > 0:
                article_dict['is_followed'] = True

        article_dict['recomments'] = []
        # # 获取相关文章推荐
        # req_article = article_reco_pb2.Article()
        # req_article.article_id = article_id
        # req_article.article_num = constants.RECOMMENDED_SIMILAR_ARTICLE_MAX
        # try:
        #     stub = article_reco_pb2_grpc.ARecommendStub(rpc_cli)
        #     resp = stub.artilcle_recommend(req_article)
        # except Exception:
        #     article_dict['recomments'] = []
        # else:
        #     reco_arts = resp.article_single_param.single_bp
        #
        #     reco_art_list = []
        #     reco_art_ids = []
        #     for art in reco_arts:
        #         reco_art_list.append({
        #             'art_id': art.article_id,
        #             'tracking': art.param
        #         })
        #         reco_art_ids.append(art.article_id)
        #
        #     reco_art_objs = Article.query.options(load_only(Article.id, Article.title)).filter(Article.id.in_(reco_art_ids)).all()
        #     reco_arts_dict = {}
        #     for art in reco_art_objs:
        #         reco_arts_dict[art.id] = art.title
        #
        #     for art in reco_art_list:
        #         art['title'] = reco_arts_dict[art['art_id']]
        #     article_dict['recomments'] = reco_art_list

        return article_dict


class ArticleListResource(Resource):
    pass


