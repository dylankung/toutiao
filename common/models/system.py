from datetime import datetime

from . import db


class Administrator(db.Model):
    """
    管理员基本信息
    """
    __tablename__ = 'administrator'

    class STATUS:
        ENABLE = 1
        DISABLE = 0

    id = db.Column('administrator_id', db.Integer, primary_key=True, doc='管理员ID')
    account = db.Column(db.String, doc='账号')
    password = db.Column(db.String, doc='密码')
    name = db.Column(db.String, doc='管理员名称')
    administrator_group_id = db.Column(db.Integer, doc='管理员角色/组ID')
    access_count = db.Column(db.Integer, default=0, doc='访问次数')
    status = db.Column(db.Integer, default=1, doc='状态')
    last_login = db.Column(db.DateTime, doc='最后登录时间')
    ctime = db.Column('create_time', db.DateTime, default=datetime.now, doc='创建时间')
    uime = db.Column('update_time', db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class AdministratorGroup(db.Model):
    """
    管理员组/角色
    """
    __tablename__ = 'administrator_group'
    class STATUS:
        ENABLE = 1
        DISABLE = 0

    id = db.Column('administrator_group_id', db.Integer, primary_key=True, doc='管理员角色/组ID')
    name = db.Column(db.Stirng, doc='角色/组')
    status = db.Column(db.Integer, default=1, doc='状态')
    remark = db.Column(db.String, doc='备注')
    ctime = db.Column('create_time', db.DateTime, default=datetime.now, doc='创建时间')
    uime = db.Column('update_time', db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class Permission(db.Model):
    """
    权限表
    """
    __tablename__ = 'permission'
    class TYPE:
        # 菜单
        MENU = 0
        # 接口
        API = 1

    id = db.Column('permission_id', db.Integer, primary_key=True, doc='权限ID')
    name = db.Column(db.Integer, doc='权限')
    type = db.Column(db.Integer, default=1, doc='权限类型')
    parent_id = db.Column(db.Integer, doc='父目录的ID')
    code = db.Column(db.String, doc='权限点代码')
    sequence = db.Column(db.Integer, default=0, doc='序列')
    ctime = db.Column('create_time', db.DateTime, default=datetime.now, doc='创建时间')
    uime = db.Column('update_time', db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class GroupPermission(db.Model):
    """
    组权限表
    """
    __tablename__ = 'group_permission'

    id = db.Column(db.Integer, primary_key=True, doc='权限ID')
    group_id = db.Column(db.Integer, doc='角色/组ID')
    permission_id = db.Column(db.Integer, doc='权限ID')
    ctime = db.Column('create_time', db.DateTime, default=datetime.now, doc='创建时间')


