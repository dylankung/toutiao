from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask_restful import inputs
from flask import current_app, g
import re
import random
from sqlalchemy import func

from utils.decorators import verify_required
from utils import parser
from models.news import Article, ArticleContent, ArticleStatistic
from models import db


class ArticleListResource(Resource):
    """
    文章
    """
    method_decorators = [verify_required]

    def _cover(self, value):
        error_msg = 'Invalid cover param.'
        if not isinstance(value, dict):
            raise ValueError(error_msg)

        cover_type = value.get('type')
        if cover_type not in (-1, 0, 1, 3):
            raise ValueError(error_msg)

        images = value.get('images')
        if not isinstance(images, list) or (cover_type != -1 and len(images) != cover_type):
            raise ValueError(error_msg)

        for image in images:
            if not image.startswith(current_app.config['QINIU_DOMAIN']):
                raise ValueError(error_msg)

        return value

    def _generate_article_cover(self, content):
        """
        生成文章封面
        :param content: 文章内容
        """
        results = re.findall(r'src=\"(' + current_app.config['QINIU_DOMAIN'] + r'[^"]+)\"', content)
        length = len(results)
        if length <= 0:
            return {'type': 0, 'images': []}
        elif length < 3:
            img_url = random.choice(results)
            return {'type': 1, 'images': [img_url]}
        else:
            random.shuffle(results)
            img_urls = results[:3]
            return {'type': 3, 'images': img_urls}

    def post(self):
        """
        发表文章
        """
        req_parser = RequestParser()
        req_parser.add_argument('draft', type=inputs.boolean, required=False, location='args')
        req_parser.add_argument('title', type=inputs.regex(r'.{5,30}'), required=True, location='json')
        req_parser.add_argument('content', type=inputs.regex(r'.+'), required=True, location='json')
        req_parser.add_argument('cover', type=self._cover, required=True, location='json')
        req_parser.add_argument('channel_id', type=parser.channel_id, required=True, location='json')
        args = req_parser.parse_args()
        content = args['content']
        cover = args['cover']
        draft = args['draft']

        # 对于自动封面，生成封面
        cover_type = cover['type']
        if cover_type == -1:
            cover = self._generate_article_cover(content)

        article = Article(
            user_id=g.user_id,
            channel_id=args['channel_id'],
            title=args['title'],
            cover=cover,
            status=Article.STATUS.DRAFT if draft else Article.STATUS.UNREVIEWED
        )
        db.session.add(article)
        db.session.flush()
        article_id = article.id

        article_content = ArticleContent(id=article_id, content=content)
        db.session.add(article_content)

        article_statistic = ArticleStatistic(id=article_id)
        db.session.add(article_statistic)

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return {'message': 'Server has something wrong.'}, 507

        # if not draft:
            # TODO 机器审核
            # TODO 新文章消息推送

        return {'id': article_id}, 201


class ArticleResource(ArticleListResource):
    """
    文章
    """
    def put(self, target):
        """
        发表文章
        """
        req_parser = RequestParser()
        req_parser.add_argument('draft', type=inputs.boolean, required=False, location='args')
        req_parser.add_argument('title', type=inputs.regex(r'.{5,30}'), required=True, location='json')
        req_parser.add_argument('content', type=inputs.regex(r'.+'), required=True, location='json')
        req_parser.add_argument('cover', type=self._cover, required=True, location='json')
        req_parser.add_argument('channel_id', type=parser.channel_id, required=True, location='json')
        args = req_parser.parse_args()
        content = args['content']
        cover = args['cover']
        draft = args['draft']

        ret = db.session.query(func.count(Article.id)).filter(Article.id == target, Article.user_id == g.user_id).first()
        if ret[0] == 0:
            return {'message': 'Invalid article.'}, 400

        # 对于自动封面，生成封面
        cover_type = cover['type']
        if cover_type == -1:
            cover = self._generate_article_cover(content)

        Article.query.filter_by(id=target).update(dict(
            channel_id=args['channel_id'],
            title=args['title'],
            cover=cover,
            status=Article.STATUS.DRAFT if draft else Article.STATUS.UNREVIEWED
        ))

        ArticleContent.query.filter_by(id=target).update(dict(content=content))

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return {'message': 'Server has something wrong.'}, 507

        # if not draft:
            # TODO 机器审核
            # TODO 新文章消息推送

        return {'id': target}, 201
