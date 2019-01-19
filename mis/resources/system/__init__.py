from flask import Blueprint
from flask_restful import Api

from utils.output import output_json


system_bp = Blueprint('system', __name__)
system_api = Api(system_bp, catch_all_404s=True)
system_api.representation('application/json')(output_json)
