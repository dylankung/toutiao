from flask import jsonify

from . import create_app
from settings.default import DefaultConfig


app = create_app(DefaultConfig, enable_config_file=True)


@app.route('/')
def route_map():
    """
    主视图，返回所有视图网址
    """
    rules_iterator = app.url_map.iter_rules()
    return jsonify({rule.endpoint: rule.rule for rule in rules_iterator})
