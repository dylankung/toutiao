from flask import Blueprint
from flask_restful import Api

from utils.output import output_json

recommend_bp = Blueprint('recommend', __name__)
recommend_api = Api(recommend_bp, catch_all_404s=True)
recommend_api.representation('application/json')(output_json)
