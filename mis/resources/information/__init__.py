from flask import Blueprint
from flask_restful import Api

from utils.output import output_json

information_bp = Blueprint('information', __name__)
information_api = Api(information_bp, catch_all_404s=True)
information_api.representation('application/json')(output_json)
