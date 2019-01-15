from flask_restful import Resource
from flask import current_app
import time

from cache import user as cache_user
from cache import article as cache_article


class IMTestResource(Resource):
    """
    系统公告
    """
    def get(self, event):
        """
        im测试
        """
        user_id = 1
        if 'f' == event:
            target = 5
            # 发送关注通知
            _user = cache_user.get_user(user_id)
            _data = {
                'user_id': user_id,
                'user_name': _user['name'],
                'user_photo': _user['photo'],
                'timestamp': int(time.time())
            }
            current_app.sio.emit('following notify', data=_data, room=str(target))

            return {'message': '已发送following notify事件'}

        elif 'l' == event:
            target = 141428
            # 发送点赞通知
            _user = cache_user.get_user(user_id)
            _article = cache_article.get_article_info(target)
            _data = {
                'user_id': user_id,
                'user_name': _user['name'],
                'user_photo': _user['photo'],
                'art_id': target,
                'art_title': _article['title'],
                'timestamp': int(time.time())
            }
            current_app.sio.emit('liking notify', data=_data, room=str(_article['aut_id']))
            return {'message': '已发送liking notify事件'}

        elif 'c' == event:
            article_id = 141428
            # 发送评论通知
            _user = cache_user.get_user(user_id)
            _article = cache_article.get_article_info(article_id)
            _data = {
                'user_id': user_id,
                'user_name': _user['name'],
                'user_photo': _user['photo'],
                'art_id': article_id,
                'art_title': _article['title'],
                'timestamp': int(time.time())
            }
            current_app.sio.emit('comment notify', data=_data, room=str(_article['aut_id']))
            return {'message': '已发送comment notify事件'}

        else:
            return {'message': '错误的事件'}, 404
