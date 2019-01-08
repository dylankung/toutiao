import logging
import time
from functools import partial

from . import sio, rpc_chat
from common import check_user_id
from rpc.chatbot import chatbot_pb2, chatbot_pb2_grpc


logger = logging.getLogger('im')


@sio.on('message')
def on_message(sid, data):
    """
    客户端发送消息时
    :param sid:
    :param data:
    :return:
    """
    rooms = sio.rooms(sid)
    assert len(rooms) == 2

    user_id = ''
    for room in rooms:
        if room == sid:
            continue
        else:
            user_id = room
            break

    assert user_id != ''

    # TODO 接入chatbot RPC服务
    stub = chatbot_pb2_grpc.ChatBotServiceStub(rpc_chat)
    req = chatbot_pb2.ReceivedMessage(
        user_id=str(user_id),
        user_message=data.get('msg', ''),
        create_time=data.get('timestamp', int(time.time()))
    )
    try:
        resp_future = stub.Chatbot.future(req)
        resp_future.add_done_callback(partial(chatbot_rpc_callback, sid=sid))
    except Exception as e:
        logger.error(e)
        msg = 'oops，我病了，容我缓一下...'
        timestamp = int(time.time())
        sio.send({'msg': msg, 'timestamp': timestamp}, room=sid)


def chatbot_rpc_callback(resp_future, sid=None):
    resp = resp_future.result()
    msg = resp.user_response
    timestamp = resp.create_time
    sio.send({'msg': msg, 'timestamp': timestamp}, room=sid)

