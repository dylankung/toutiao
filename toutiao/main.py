from . import create_app
from settings.default import DefaultConfig


app = create_app(DefaultConfig, enable_config_file=True)
