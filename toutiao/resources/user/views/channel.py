from flask_restful import Resource


class ChannelListResource(Resource):
    """
    用户频道
    """
    def post(self):
        """
        编辑用户频道
        """
        pass

    def get(self):
        """
        获取用户频道
        """
        pass

    def delete(self):
        """
        批量删除用户频道
        """
        pass

    def put(self):
        """
        批量修改用户频道
        """
        pass


class ChannelResource(Resource):
    """
    用户频道
    """
    def put(self):
        """
        修改指定用户频道
        """
        pass

    def delete(self):
        """
        删除指定用户频道
        """
        pass
