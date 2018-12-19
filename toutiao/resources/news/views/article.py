from flask_restful import Resource, abort
from flask_restful import marshal, fields
from flask import g, current_app
from sqlalchemy.orm import load_only
import pickle
from redis.exceptions import RedisError
import time
from flask_restful.reqparse import RequestParser
from flask_restful import inputs
import re
import random
from sqlalchemy import func

from models.news import Article, ArticleContent
from models.user import User, Relation
from toutiao.main import redis_cli, rpc_cli
from rpc import article_reco_pb2_grpc
from rpc import article_reco_pb2
from .. import constants
from utils import parser
from cache import article as cache_article
from cache import user as cache_user
from models import db
from utils.decorators import login_required


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
            # TODO 使用用户缓存
            # ret = db.session.query(func.count(Relation.id))\
            #     .filter_by(user_id=user_id, target_user_id=article_dict['aut_id'], relation=Relation.RELATION.FOLLOW)\
            #     .first()
            # if ret[0] > 0:
            #     article_dict['is_followed'] = True
            article_dict['is_followed'] = cache_user.determine_user_follows_target(user_id, article_dict['aut_id'])

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

    def _generate_article_cover(self, article_id):
        """
        生成文章封面(处理测试数据专用）
        :param article_id: 文章id
        """
        article = Article.query.options(load_only(Article.cover)).filter_by(id=article_id).first()
        if article.cover['type'] > 0:
            return
        content = ArticleContent.query.filter_by(id=article_id).first()
        if content is None:
            return
        results = re.findall(r'src=\"http([^"]+)\"', content.content)
        length = len(results)
        if length <= 0:
            return
        elif length < 3:
            img_url = random.choice(results)
            img_url = 'http' + img_url
            Article.query.filter_by(id=article_id).update({'cover': {'type': 1, 'images': [img_url]}})
            db.session.commit()
        else:
            random.shuffle(results)
            img_urls = results[:3]
            img_urls = ['http'+img_url for img_url in img_urls]
            Article.query.filter_by(id=article_id).update({'cover': {'type': 3, 'images': img_urls}})
            db.session.commit()

    def get(self):
        """
        获取文章列表
        /v1_0/articles?channel_id&page&per_page
        """
        qs_parser = RequestParser()
        qs_parser.add_argument('channel_id', type=parser.channel_id, required=True, location='args')
        qs_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        qs_parser.add_argument('per_page', type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
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
            # self._generate_article_cover(article_id)
            article = cache_article.get_article_info(article_id)
            if article:
                results.append(article)

        return {'page': page, 'per_page': per_page, 'results': results}


class UserArticleListResource(Resource):
    """
    用户文章列表
    """
    def get(self, user_id):
        """
        获取user_id 用户的文章数据
        """
        exist = cache_user.determine_user_exists(user_id)
        if not exist:
            return {'message': 'Invalid request.'}, 400
        qs_parser = RequestParser()
        qs_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        qs_parser.add_argument('per_page', type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                                 constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                                 'per_page'),
                               required=False, location='args')
        args = qs_parser.parse_args()
        page = 1 if args.page is None else args.page
        per_page = args.per_page if args.per_page else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

        results = []
        articles = cache_user.get_user_articles(user_id)
        total_count = len(articles)
        req_articles = articles[(page - 1) * per_page:page * per_page]
        for article_id in req_articles:
            article = cache_article.get_article_info(article_id)
            if article:
                results.append(article)

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}


class CurrentUserArticleListResource(Resource):
    """
    当前用户的文章列表
    """
    method_decorators = [login_required]

    def get(self):
        """
        获取当前用户的文章列表
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

        results = []
        articles = cache_user.get_user_articles(g.user_id)
        total_count = len(articles)
        req_articles = articles[(page - 1) * per_page:page * per_page]
        for article_id in req_articles:
            article = cache_article.get_article_info(article_id)
            if article:
                results.append(article)

        return {'total_count': total_count, 'page': page, 'per_page': per_page, 'results': results}

