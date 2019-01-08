import logging
import time

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
        resp = stub.Chatbot(req, timeout=3)
    except Exception as e:
        logger.error(e)
        msg = 'oops，我病了，容我缓一下...'
        timestamp = int(time.time())
    else:
        msg = resp.user_response
        timestamp = resp.create_time

    sio.send({'msg': msg, 'timestamp': timestamp}, room=sid)
