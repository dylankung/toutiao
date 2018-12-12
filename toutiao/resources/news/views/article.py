from flask_restful import Resource, abort
from flask_restful import marshal, fields
from flask import g, current_app
from sqlalchemy.orm import load_only
import pickle
from redis.exceptions import RedisError
import time
from flask_restful.reqparse import RequestParser
from flask_restful.inputs import positive, int_range

from models.news import Article
from models.user import User, Follow
from toutiao.main import redis_cli, rpc_cli
from rpc import article_reco_pb2_grpc
from rpc import article_reco_pb2
from .. import constants
from utils import parser
from cache import article as cache_article


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

        # TODO 文章做全局缓存层

        # 查询文章数据
        r_cache = redis_cli['art_cache']
        article_bytes = r_cache.get('art:{}'.format(article_id))
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
                r_cache.setex('art:{}'.format(article_id), constants.CACHE_ARTICLE_EXPIRE, article_cache)
            except RedisError:
                pass

        # 非匿名用户添加用户的阅读历史
        if user_id:
            r_his = redis_cli['read_his']
            pl = r_his.pipeline()
            pl.sadd('users', user_id)
            pl.hset('his:{}'.format(user_id), article_id, int(time.time()))
            pl.execute()

        # 查询关注
        article_dict['is_followed'] = False
        if user_id:
            ret = Follow.query.filter_by(user_id=user_id, following_user_id=article_dict['aut_id'], is_deleted=False).count()
            if ret > 0:
                article_dict['is_followed'] = True

        # TODO 查询登录用户对文章的态度（点赞or不喜欢）

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
    """
    文章列表数据
    """
    def _get_recommended_articles(self, channel_id, page, per_page):
        """
        获取推荐的文章
        :param channel_id: 频道id
        :param page: 页数
        :param per_page: 每页数量
        :return: [article_id, ...]
        """
        # TODO 接入推荐系统后 需要改写
        offset = (page - 1) * per_page
        articles = Article.query.options(load_only()).filter_by(channel_id=channel_id, status=Article.STATUS.APPROVED)\
            .order_by(Article.id).offset(offset).limit(per_page).all()
        if articles:
            return [article.id for article in articles]
        else:
            return []

    def get(self):
        """
        获取文章列表
        /v1_0/articles?channel_id&page&per_page
        """
        qs_parser = RequestParser()
        qs_parser.add_argument('channel_id', type=parser.channel_id, required=True, location='args')
        qs_parser.add_argument('page', type=positive, required=False, location='args')
        qs_parser.add_argument('per_page', type=int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                          constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                          'per_page'),
                               required=False, location='args')
        args = qs_parser.parse_args()
        channel_id = args.channel_id
        page = 1 if args.page is None else args.page
        per_page = args.per_page if args.per_page else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

        article_id_li = []
        results = []

        if page == 1:
            # 第一页
            ret = cache_article.get_channel_top_articles(channel_id)
            if ret:
                article_id_li = ret

        # 获取推荐文章列表
        ret = self._get_recommended_articles(channel_id, page, per_page)
        if article_id_li:
            article_id_set = set(article_id_li)
            # 去重
            for article_id in ret:
                if article_id in article_id_set:
                    continue
                article_id_li.append(article_id)
        else:
            article_id_li = ret

        # 查询文章
        for article_id in article_id_li:
            article = cache_article.get_article_info(article_id)
            if article:
                results.append(article)

        return {'page': page, 'per_page': per_page, 'results': results}


