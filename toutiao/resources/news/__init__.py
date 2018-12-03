from flask import Blueprint
from flask_restful import Api

from .views import article, action
from utils.output import output_json


news_bp = Blueprint('news', __name__)
news_api = Api(news_bp, catch_all_404s=True)
news_api.representation('application/json')(output_json)


news_api.add_resource(article.ArticleResource, '/v1_0/articles/<int(min=1):article_id>',
                      endpoint='Article')

news_api.add_resource(action.CollectionListResource, '/v1_0/article/collections',
                      endpoint='Collections')

news_api.add_resource(action.CollectionResource, '/v1_0/article/collections/<int(min=1):target>',
                      endpoint='Collection')


