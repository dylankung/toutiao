from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import current_app, g
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import load_only

from utils.decorators import login_required
from utils import parser
from utils.storage import upload_image
from models.user import Material
from models import db


class ImageListResource(Resource):
    """
    图片资源
    """
    method_decorators = [login_required]

    def post(self):
        """
        上传图片文件
        """
        req_parser = RequestParser()
        req_parser.add_argument('image', type=parser.image_file, required=True, location='files')
        file = req_parser.parse_args()

        user_id = g.user_id

        try:
            image_key = upload_image(file['image'].read())
        except Exception as e:
            current_app.logger.error('upload failed {}'.format(e))
            return {'message': 'Uploading profile photo image failed.'}, 507

        # TODO 图片默认审核通过
        query = insert(Material).values(
            user_id=user_id,
            type=Material.TYPE.IMAGE,
            hash=image_key,
            url=image_key,
            status=Material.STATUS.APPROVED
        ).on_duplicate_key_update(status=Material.STATUS.APPROVED)

        db.session.execute(query)
        db.session.commit()

        material = Material.query.options(load_only(Material.id, Material.url))\
            .filter_by(user_id=user_id, hash=image_key).first()
        return {'id': material.id, 'url': current_app.config['QINIU_DOMAIN'] + material.url}, 201

