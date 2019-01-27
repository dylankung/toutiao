from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask_restful import inputs, marshal, fields
from flask import g, request, current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
import traceback


from utils.decorators import mis_permission_required
from models.system import MisPermission, MisAdministrator
from utils import parser
from models import db
from . import constants


class AdministratorListResource(Resource):
    """
    管理员管理
    """
    administrators_fields = {
        'administrator_id': fields.Integer(attribute='id'),
        'account': fields.String(attribute='account'),
        'name': fields.String(attribute='name'),
        'group_name': fields.String(attribute='group.name'),
        'group_id': fields.Integer(attribute='group_id'),
        'access_count': fields.Integer(attribute='access_count'),
        'status': fields.Integer(attribute='status'),
        'last_login': fields.Integer(attribute='last_login')
    }
    method_decorators = {
        'get': [mis_permission_required('administrator-list-get')],
        'post': [mis_permission_required('administrator-list-post')],
    }

    def post(self):
        """
        添加管理员
        """
        json_parser = RequestParser()
        json_parser.add_argument('account', type=parser.mis_account, required=True, location='json')
        json_parser.add_argument('password', type=parser.mis_password, required=True, location='json')
        json_parser.add_argument('group_id', type=parser.mis_group_id, required=True, location='json')
        json_parser.add_argument('name', required=True, location='json')
        args = json_parser.parse_args()
        administrator = MisAdministrator.query.filter_by(account=args.account).first()
        if administrator:
            return {'message': '{} already exists'.format(args.account)}

        administrator = MisAdministrator(account=args.account,
                                         password=generate_password_hash(args.password),
                                         name=args.name,
                                         group_id=args.group_id)
        try:
            db.session.add(administrator)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {'account': args.account,
                'name': args.name}, 201

    def get(self):
        """
        管理员查询
        """
        args_parser = RequestParser()
        args_parser.add_argument('keyword', location='args')
        args_parser.add_argument('status', type=inputs.int_range(0, 1), location='args')
        args_parser.add_argument('page', type=inputs.positive, required=False, location='args')
        args_parser.add_argument('per_page', type=inputs.int_range(constants.PER_PAGE_MIN,
                                                                 constants.PER_PAGE_MAX,
                                                                 'per_page'),
                               required=False, location='args')
        args = args_parser.parse_args()
        page = constants.DEFAULT_PAGE if args.page is None else args.page
        per_page = constants.DEFAULT_PER_PAGE if args.per_page is None else args.per_page

        administrators = MisAdministrator.query
        if args.status is not None:
            administrators = administrators.filter_by(status=args.status)
        if args.keyword:
            administrators = administrators.filter(or_(MisAdministrator.account.like('%' + args.keyword + '%'),
                                                       MisAdministrator.name.like('%' + args.keyword + '%')))
        total_count = administrators.count()
        administrators = administrators.order_by(MisAdministrator.utime.desc())\
                .offset(per_page * (page - 1)).limit(per_page).all()
        ret = marshal(administrators, AdministratorListResource.administrators_fields, envelope='administrators')
        ret['total_count'] = total_count
        return ret

    def delete(self):
        """
        批量删除管理员
        """
        json_parser = RequestParser()
        json_parser.add_argument('administrator_ids', action='append', type=inputs.positive, required=True, location='json')
        args = json_parser.parse_args()

        MisAdministrator.query.filter(MisAdministrator.id.in_(args.administrator_ids)).delete(synchronize_session=False)
        db.session.commit()
        return {'message': 'OK'}, 204


class AdministratorResource(Resource):
    """
    管理员管理
    """
    method_decorators = {
        'get': [mis_permission_required('administrator-get')],
        'put': [mis_permission_required('administrator-put')],
        'delete': [mis_permission_required('administrator-delete')],
    }

    def get(self, target):
        """
        获取管理员详情
        """
        administrator = MisAdministrator.query.filter_by(id=target).first()
        if not administrator:
            return {'message': 'Invalid administrator id.'}, 400
        return marshal(administrator, AdministratorListResource.administrators_fields)

    def put(self, target):
        """
        修改id=target管理员信息
        """
        json_parser = RequestParser()
        json_parser.add_argument('account', type=parser.mis_account, location='json')
        json_parser.add_argument('password', type=parser.mis_password, location='json')
        json_parser.add_argument('name', location='json')
        json_parser.add_argument('group_id', type=parser.mis_group_id, location='json')
        json_parser.add_argument('status', type=inputs.int_range(0, 1), location='json')

        json_parser.add_argument('email', type=parser.email, location='json')
        json_parser.add_argument('mobile', type=parser.mobile, location='json')
        json_parser.add_argument('current_password', type=parser.mis_password, location='json')

        args = json_parser.parse_args()
        print(args)
        administrator = MisAdministrator.query.filter_by(id=target).first()
        if not administrator:
            return {'message': 'Invalid administrator id.'}, 403

        if args.account and args.account != administrator.account:
            if MisAdministrator.query.filter_by(account=args.account).first():
                return {'message': '{} already exists'.format(args.account)}
            administrator.account = args.account
        if args.password:
            if target == g.administrator_id \
                    and administrator.password != generate_password_hash(args.current_password):
                return {'message': 'Current password error.'}, 403

            administrator.password = generate_password_hash(args.password)
        if args.name:
            administrator.name = args.name
        if args.group_id:
            administrator.group_id = args.group_id
        if args.status is not None:
            administrator.status = args.status
        if args.email:
            administrator.email = args.email
        if args.mobile:
            administrator.mobile = args.mobile

        try:
            db.session.add(administrator)
            db.session.commit()
        except:
            db.session.rollback()
            raise

        return marshal(administrator, AdministratorListResource.administrators_fields), 201

    def delete(self, target):
        """
        删除id=target管理员信息
        """
        MisAdministrator.query.filter_by(id=target).delete(synchronize_session=False)
        db.session.commit()
        return {'message': 'OK'}, 204
