import logging
import time

from . import sio
from common import check_user_id


logger = logging.getLogger('im')


__NAMESPACE = '/chatbot'


@sio.on('connect', namespace=__NAMESPACE)
def on_connect(sid, environ):
    """
    上线时
    :param sid:
    :param environ: WSGI dict
    :return:
    """
    print('chatbot: {}'.format(sid))
    user_id = check_user_id(environ, sio.JWT_SECRET)

    if not user_id:
        return False

    sio.enter_room(sid, str(user_id), namespace=__NAMESPACE)

    timestamp = time.time()
    msg = '您好，传智黑客为您服务，请问您有什么问题？'
    sio.send({'msg': msg, 'timestamp': timestamp}, room=sid, namespace=__NAMESPACE)


@sio.on('disconnect', namespace=__NAMESPACE)
def on_disconnect(sid):
    """
    下线时
    :param sid:
    :return:
    """
    rooms = sio.rooms(sid, namespace=__NAMESPACE)
    for room in rooms:
        sio.leave_room(sid, room, namespace=__NAMESPACE)


@sio.on('message', namespace=__NAMESPACE)
def on_message(sid, data):
    """
    客户端发送消息时
    :param sid:
    :param data:
    :return:
    """
    rooms = sio.rooms(sid, namespace=__NAMESPACE)
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
    timestamp = time.time()
    msg = '我已知悉，请容我三思[]...'.format(timestamp)

    sio.send({'msg': msg, 'timestamp': timestamp}, room=sid, namespace=__NAMESPACE)
