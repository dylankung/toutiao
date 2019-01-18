from flask_restful import Resource

from utils.decorators import verify_required


class ArticleListResource(Resource):
    """
    文章
    """
    method_decorators = [verify_required]

    def post(self):
        """
        发表文章
        """
        pass
