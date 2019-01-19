from flask import Blueprint
from flask_restful import Api

from utils.output import output_json


statistics_bp = Blueprint('statistics', __name__)
statistics_api = Api(statistics_bp, catch_all_404s=True)
statistics_api.representation('application/json')(output_json)
