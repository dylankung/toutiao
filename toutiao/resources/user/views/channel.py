from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import request, g, current_app
from sqlalchemy.orm import load_only, contains_eager
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.mysql import insert
from flask_restful import fields, marshal
from flask_restful import inputs

from utils.decorators import login_required, validate_token_if_using
from models.news import UserChannel, Channel
from models import db
from cache import channel as cache_channel


class ChannelListResource(Resource):
    """
    用户频道
    """
    method_decorators = {
        'post': [login_required],
        'put': [login_required],
        'patch': [login_required],
        'delete': [login_required],
        'get': [validate_token_if_using]
    }

    def _parse_channel_list(self):
        """
        检验参数是否是合法的channel 列表
        """
        req = request.get_json(force=True)
        if not req or not req.get('channels'):
            raise ValueError('Channels param is required.')

        channel_list = req['channels']
        if not isinstance(channel_list, list):
            raise ValueError('Invalid channels param.')

        try:
            channel_id_li = [channel['id'] for channel in channel_list]
            channel_seq_li = [int(channel['seq']) for channel in channel_list]
        except Exception:
            raise ValueError('Invalid channels param.')

        channel_id_set = set(channel_id_li)
        if len(channel_id_li) > len(channel_id_set):
            raise ValueError('Repeated channels occurred.')

        r = current_app.redis_cli['art_cache']
        all_channel_id = r.zrange('channel:id', 0, -1)
        if all_channel_id:
            all_channel_id = [int(channel_id) for channel_id in all_channel_id]
        else:
            all_channel = Channel.query.options(load_only(Channel.id)).filter_by(is_visible=True).all()
            all_channel_id = [channel.id for channel in all_channel]

        diff = channel_id_set - set(all_channel_id)
        if len(diff) > 0:
            raise ValueError('Invalid channels param.')

        for seq in channel_seq_li:
            if seq < 0:
                raise ValueError('Invalid channel sequence param.')

        return channel_list

    def post(self):
        """
        编辑用户频道，首次
        """
        try:
            channel_list = self._parse_channel_list()
        except ValueError as e:
            return {'message': '{}'.format(e)}, 400

        user_id = g.user_id
        try:
            for channel in channel_list:
                new_channel = UserChannel(user_id=user_id,
                                          channel_id=channel['id'],
                                          sequence=channel['seq'])
                db.session.add(new_channel)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'message': 'Some conflict user channels occurred.'}, 409

        return {'channels': channel_list}, 201

    def put(self):
        """
        修改用户频道，重置
        """
        try:
            channel_list = self._parse_channel_list()
        except ValueError as e:
            return {'message': '{}'.format(e)}, 400

        user_id = g.user_id

        # Update user's all previous channels to be deleted.
        UserChannel.query.filter_by(user_id=user_id, is_deleted=False).update({'is_deleted': True})

        for channel in channel_list:
            query = insert(UserChannel).values(user_id=user_id,
                                               channel_id=channel['id'],
                                               sequence=channel['seq'])\
                .on_duplicate_key_update(sequence=channel['seq'], is_deleted=False)
            db.session.execute(query)

        db.session.commit()

        return {'channels': channel_list}, 201

    def patch(self):
        """
        修改用户频道，部分
        """
        try:
            channel_list = self._parse_channel_list()
        except ValueError as e:
            return {'message': '{}'.format(e)}, 400

        user_id = g.user_id

        for channel in channel_list:
            query = insert(UserChannel).values(user_id=user_id,
                                               channel_id=channel['id'],
                                               sequence=channel['seq'])\
                .on_duplicate_key_update(sequence=channel['seq'], is_deleted=False)
            db.session.execute(query)

        db.session.commit()

        return {'channels': channel_list}, 201

    # For response format.
    channel_fields = {
        'id': fields.Integer(attribute='channel_id'),
        'name': fields.String(attribute='channel.name')
    }

    def _get_recommendation_channel(self):
        """
        获取0号「推荐」频道
        """
        return {'id': 0, 'name': '推荐'}
        # return {}

    def get(self):
        """
        获取用户频道
        """
        user_id = g.user_id
        if user_id:
            # error
            # user_channels = UserChannel.query.options(load_only(UserChannel.channel_id),
            #                                           joinedload(UserChannel.channel, innerjoin=True)
            #                                           .load_only(Channel.name))\
            #     .filter(UserChannel.user_id == user_id, UserChannel.is_deleted == False, Channel.is_visible == True)\
            #     .order_by(UserChannel.sequence).all()

            user_channels = UserChannel.query.join(UserChannel.channel).options(load_only(UserChannel.channel_id),
                                                                                contains_eager(UserChannel.channel)
                                                                                .load_only(Channel.name))\
                .filter(UserChannel.user_id == user_id, UserChannel.is_deleted == False, Channel.is_visible == True)\
                .order_by(UserChannel.sequence).all()

            ret = marshal(user_channels, ChannelListResource.channel_fields, envelope='channels')

            recommendation_channel = self._get_recommendation_channel()
            if recommendation_channel:
                ret['channels'].insert(0, recommendation_channel)

            return ret

        else:
            # Return default channels
            default_channels = cache_channel.get_default_channels()

            recommendation_channel = self._get_recommendation_channel()
            if recommendation_channel:
                default_channels.insert(0, recommendation_channel)

            return {'channels': default_channels}

    def delete(self):
        """
        批量删除用户频道
        """
        json_parser = RequestParser()
        json_parser.add_argument('channels', action='append', type=inputs.positive, required=True, location='json')
        args = json_parser.parse_args()
        channel_id_li = args.channels
        user_id = g.user_id
        # Using synchronize_session=False when update many objects to
        # indicate that Sqlalchemy does not need to trace new data.
        UserChannel.query.filter(UserChannel.user_id == user_id, UserChannel.channel_id.in_(channel_id_li))\
            .update({'is_deleted': True}, synchronize_session=False)
        db.session.commit()
        return {'message': 'OK'}, 204


class ChannelResource(Resource):
    """
    用户频道
    """
    method_decorators = [login_required]

    def put(self, target):
        """
        修改指定用户频道
        """
        user_id = g.user_id
        json_parser = RequestParser()
        json_parser.add_argument('seq', type=inputs.positive, required=True, location='json')
        args = json_parser.parse_args()

        exist = cache_channel.determine_channel_exists(target)
        if not exist:
            return {'message': 'Invalid channel id.'}, 400

        query = insert(UserChannel).values(user_id=user_id,
                                           channel_id=target,
                                           sequence=args.seq)\
            .on_duplicate_key_update(sequence=args.seq, is_deleted=False)
        db.session.execute(query)

        db.session.commit()

        return {'id': target, 'seq': args.seq}, 201

    def delete(self, target):
        """
        删除指定用户频道
        """
        user_id = g.user_id
        UserChannel.query.filter_by(user_id=user_id, channel_id=target).update({'is_deleted': True})
        db.session.commit()
        return {'message': 'OK'}, 204
