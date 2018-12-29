import logging
from werkzeug.wrappers import Request
import time

from . import sio
from utils.jwt_util import verify_jwt

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
    # 判断用户身份
    request = Request(environ)
    authorization = request.headers.get('Authorization')
    user_id = None
    if authorization and authorization.startswith('Bearer '):
        token = authorization.strip()[7:]
        payload = verify_jwt(token, secret=sio.JWT_SECRET)
        if payload:
            user_id = payload.get('user_id')
    elif authorization and authorization.startswith('Anony '):
        user_id = authorization.strip()[6:]

    if user_id:
        print(user_id)
        sio.enter_room(sid, str(user_id), namespace=__NAMESPACE)
    else:
        return False


@sio.on('disconnect', namespace=__NAMESPACE)
def on_disconnect(sid):
    """
    下线时
    :param sid:
    :return:
    """
    rooms = sio.rooms(sid, namespace=__NAMESPACE)
    print(rooms)
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
    print(rooms)
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
