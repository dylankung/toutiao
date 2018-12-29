import socketio
import eventlet.wsgi

from im.common import get_config, create_logger

sio = socketio.Server()


def run(port):
    """
    运行
    :param port: 端口
    :return:
    """
    config = get_config()
    log = create_logger(config)

    # create a Socket.IO server
    global sio
    sio = socketio.Server(async_mode='eventlet', logger=log, ping_timeout=300)

    sio.JWT_SECRET = config.JWT_SECRET

    # 添加处理
    from . import chatbot, notify

    app = socketio.Middleware(sio)

    eventlet.wsgi.server(eventlet.listen(('', port)), app, log=log)


