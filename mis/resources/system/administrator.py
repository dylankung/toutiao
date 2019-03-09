from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask_restful import inputs, marshal, fields
from flask import g, request, current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
import traceback


from utils.decorators import mis_permission_required
from models.system import *
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
        'email': fields.String(attribute='email'),
        'mobile': fields.String(attribute='mobile'),
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
            return {'message': '{} already exists'.format(args.account)}, 403

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
        args_parser.add_argument('order_by', location='args')
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
        if args.order_by is not None:
            if args.order_by == 'id':
                administrators = administrators.order_by(MisAdministrator.id.asc())
        else:
            administrators = administrators.order_by(MisAdministrator.utime.desc())
        total_count = administrators.count()
        administrators = administrators.offset(per_page * (page - 1)).limit(per_page).all()

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


class AdministratorInitResource(Resource):
    """
    初始化
    """
    def _get_init_permissions(self):
        permissions = [
            {
                "name": "数据统计",
                "code": "/data_statistics_manager",
                'type': 0
            },
            {
                "name": "系统管理",
                "code": "/system_manager",
                'type': 0
            },
            {
                "name": "推荐系统",
                "code": "/recommend_system_manager",
                'type': 0
            },
            {
                "name": "permission-list-get",
                "code": "permission-list-get"
            },
            {
                "name": "administrator-list-get",
                "code": "administrator-list-get"
            },
            {
                "name": "permission-get",
                "code": "permission-get"
            },
            {
                "name": "group-list-get",
                "code": "group-list-get"
            },
            {
                "name": "permission-list-post",
                "code": "permission-list-post"
            },
            {
                "name": "group-put-hahah",
                "code": "group-put"
            },
            {
                "name": "operationlog-get",
                "code": "operationlog-get"
            },
            {
                "name": "userlist-get",
                "code": "userlist-get"
            },
            {
                "name": "userlist-post",
                "code": "userlist-post"
            },
            {
                "name": "user-get",
                "code": "user-get"
            },
            {
                "name": "legalize-list-get",
                "code": "legalize-list-get"
            },
            {
                "name": "legalize-list-post",
                "code": "legalize-list-post"
            },
            {
                "name": "legalize-list-put",
                "code": "legalize-list-put"
            },
            {
                "name": "legalize-get",
                "code": "legalize-get"
            },
            {
                "name": "administrator-delete",
                "code": "administrator-delete"
            },
            {
                "name": "administrator-list-post",
                "code": "administrator-list-post"
            },
            {
                "name": "administrator-get",
                "code": "administrator-get"
            },
            {
                "name": "userlist-put",
                "code": "userlist-put"
            },
            {
                "name": "administrator-put",
                "code": "administrator-put"
            },
            {
                "name": "channel-list-get",
                "code": "channel-list-get"
            },
            {
                "name": "channel-list-post",
                "code": "channel-list-post"
            },
            {
                "name": "channel-list-put",
                "code": "channel-list-put"
            },
            {
                "name": "channel-list-delete",
                "code": "channel-list-delete"
            },
            {
                "name": "permission-delete",
                "code": "permission-delete"
            },
            {
                "name": "permission-put",
                "code": "permission-put"
            },
            {
                "name": "sensitive-word-list-get",
                "code": "sensitive-word-list-get"
            },
            {
                "name": "sensitive-word-list-post",
                "code": "sensitive-word-list-post"
            },
            {
                "name": "sensitive-word-get",
                "code": "sensitive-word-get"
            },
            {
                "name": "sensitive-word-post",
                "code": "sensitive-word-post"
            },
            {
                "name": "sensitive-word-delete",
                "code": "sensitive-word-delete"
            },
            {
                "name": "statistics-basic-get",
                "code": "statistics-basic-get"
            },
            {
                "name": "statistics-search-get",
                "code": "statistics-search-get"
            },
            {
                "name": "statistics-search-total-get",
                "code": "statistics-search-total-get"
            },
            {
                "name": "statistics-sales-total-get",
                "code": "statistics-sales-total-get"
            },
            {
                "name": "statistics-read-source-total-get",
                "code": "statistics-read-source-total-get"
            },
            {
                "name": "article-list-get",
                "code": "article-list-get"
            },
            {
                "name": "article-list-put",
                "code": "article-list-put"
            },
            {
                "name": "article-get",
                "code": "article-get"
            },
            {
                "name": "group-list-post",
                "code": "group-list-post"
            },
            {
                "name": "group-delete",
                "code": "group-delete"
            },
            {
                "name": "group-get",
                "code": "group-get"
            }
        ]
        return permissions

    def _get_permission_ids(self):
        permissions = self._get_init_permissions()
        permissions_ids = []
        for p in permissions:
            obj = MisPermission.query.filter_by(name=p['name']).first()
            if not obj:
                obj = MisPermission(name=p['name'], code=p['code'], type=p.get('type', 1))
                db.session.add(obj)
                db.session.commit()
            permissions_ids.append(obj.id)
        return permissions_ids

    def _get_group_id(self):
        name = '管理员'
        group = MisAdministratorGroup.query.filter_by(name=name).first()
        if not group:
            group = MisAdministratorGroup(name=name)
            db.session.add(group)
            db.session.commit()
        permissions_ids = self._get_permission_ids()
        for pid in permissions_ids:
            gp = MisGroupPermission.query.filter_by(group_id=group.id, permission_id=pid).first()
            if not gp:
                gp = MisGroupPermission(group_id=group.id, permission_id=pid)
                db.session.add(gp)
                db.session.commit()
        return group.id

    def _create_init_administrator(self):
        account = 'cz_admin'
        password = 'cs_itcast'
        name = '初始化管理员'
        group_id = self._get_group_id()
        admin = MisAdministrator.query.filter_by(account=account).first()
        if not admin:
            admin = MisAdministrator(account=account,
                                     password=generate_password_hash(password),
                                     group_id=group_id,
                                     name=name)
            db.session.add(admin)
            db.session.commit()

    def _mis_init(self):
        key = 'mis_init'
        cli = current_app.redis_cli['comm_cache']
        if not cli.get(key):
            cli.setex(key, 60, 1)
            print(key)
            self._create_init_administrator()

    def get(self):
        """
        创建初始权限、组、管理员
        :return:
        """
        # mis系统初始化
        if current_app.config.get('IS_INIT'):
            self._mis_init()
        return {'message': 'ok'}

