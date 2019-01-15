from flask import Blueprint
from flask_restful import Api

from . import material, channel
from utils.output import output_json

news_bp = Blueprint('news', __name__)
news_api = Api(news_bp, catch_all_404s=True)
news_api.representation('application/json')(output_json)


news_api.add_resource(material.ImageListResource, '/v1_0/user/images',
                      endpoint='UserImages')

news_api.add_resource(material.ImageResource, '/v1_0/user/images/<int(min=1):target>',
                      endpoint='UserImage')

news_api.add_resource(channel.ChannelListResource, '/v1_0/channels',
                      endpoint='Channels')
