from flask import Blueprint
from flask_restful import Api

from .views import article, collection, liking, dislike, report, comment
from utils.output import output_json


news_bp = Blueprint('news', __name__)
news_api = Api(news_bp, catch_all_404s=True)
news_api.representation('application/json')(output_json)


news_api.add_resource(article.ArticleResource, '/v1_0/articles/<int(min=1):article_id>',
                      endpoint='Article')

news_api.add_resource(collection.CollectionListResource, '/v1_0/article/collections',
                      endpoint='ArticleCollections')

news_api.add_resource(collection.CollectionResource, '/v1_0/article/collections/<int(min=1):target>',
                      endpoint='ArticleCollection')

news_api.add_resource(liking.ArticleLikingListResource, '/v1_0/article/likings',
                      endpoint='ArticleLikings')

news_api.add_resource(liking.ArticleLikingResource, '/v1_0/article/likings/<int(min=1):target>',
                      endpoint='ArticleLiking')

news_api.add_resource(dislike.DislikeListResource, '/v1_0/article/dislikes',
                      endpoint='ArticleDislikes')

news_api.add_resource(dislike.DislikeResource, '/v1_0/article/dislikes/<int(min=1):target>',
                      endpoint='ArticleDislike')

news_api.add_resource(report.ReportListResource, '/v1_0/article/reports',
                      endpoint='ArticleReports')

news_api.add_resource(comment.CommentListResource, '/v1_0/comments',
                      endpoint='Comments')

news_api.add_resource(liking.CommentLikingListResource, '/v1_0/comment/likings',
                      endpoint='CommentLikings')

news_api.add_resource(liking.CommentLikingResource, '/v1_0/comment/likings/<int(min=1):target>',
                      endpoint='CommentLiking')

