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
    logger.info('received msg:{} from user_id:{}'.format(data, sid))

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
    logger.info('user_id: {}'.format(user_id))

    # TODO 接入chatbot RPC服务
    try:
        logger.info('stub grpc')
        stub = chatbot_pb2_grpc.ChatBotServiceStub(rpc_chat)
        logger.info('req grpc')
        req = chatbot_pb2.ReceivedMessage(
            user_id=str(user_id),
            user_message=data.get('msg', ''),
            create_time=data.get('timestamp', int(time.time()))
        )
    except Exception as e:
        logger.error(e)
        return

    # # 同步调用
    # try:
    #     resp = stub.Chatbot(req, timeout=3)
    # except Exception as e:
    #     logger.error(e)
    #     msg = 'oops，我病了，容我缓一下...'
    #     timestamp = int(time.time())
    # else:
    #     msg = resp.user_response
    #     timestamp = resp.create_time
    #
    # sio.send({'msg': msg, 'timestamp': timestamp}, room=sid)

    # 异步调用
    try:
        logger.info('enter grpc')
        resp_future = stub.Chatbot.future(req, timeout=3)
        logger.info('call add_done_callback grpc')
        resp_future.add_done_callback(partial(chatbot_rpc_callback, sid=sid))
        logger.info('finish add_done_callback grpc')
    except Exception as e:
        logger.error(e)
        msg = 'oops，我病了，容我缓一下...'
        timestamp = int(time.time())
        logger.info('send msg:{} to sid:{}'.format(msg, sid))
        sio.send({'msg': msg, 'timestamp': timestamp}, room=sid)


def chatbot_rpc_callback(resp_future, sid=None):
    logger.info('enter chatbot_rpc_callback grpc')
    try:
        resp = resp_future.result(timeout=3)
    except Exception as e:
        logger.error(e)
        msg = 'oops，我病了，容我缓一下...'
        timestamp = int(time.time())
        logger.info('send msg:{} to sid:{}'.format(msg, sid))
        sio.send({'msg': msg, 'timestamp': timestamp}, room=sid)
    else:
        logger.info('enter chatbot_rpc_callback else grpc')
        msg = resp.user_response
        timestamp = resp.create_time
        logger.info('send msg:{} to sid:{}'.format(msg, sid))
        sio.send({'msg': msg, 'timestamp': timestamp}, room=sid)
    logger.info('exit chatbot_rpc_callback grpc')


