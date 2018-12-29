from flask import Flask

from utils import constants


def create_app(config, enable_config_file=False):
    """
    创建应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: Flask应用
    """
    app = Flask(__name__)
    app.config.from_object(config)
    if enable_config_file:
        app.config.from_envvar(constants.GLOBAL_SETTING_ENV_NAME, silent=True)

    return app
