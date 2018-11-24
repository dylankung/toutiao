from datetime import datetime

from . import db


class UserBasic(db.Model):
    """
    用户基本信息
    """
    __tablename__ = 'user_basic'

    user_id = db.Column(db.Integer, primary_key=True, doc='用户ID')
    mobile = db.Column(db.String, doc='手机号')
    password = db.Column(db.String, doc='密码')
    user_name = db.Column(db.String, doc='昵称')
    profile_photo = db.Column(db.String, doc='头像')
    last_login = db.Column(db.DateTime, doc='最后登录时间')
    is_media = db.Column(db.Boolean, default=False, doc='是否是自媒体')
    post_count = db.Column(db.Integer, default=0, doc='发帖数')
    following_count = db.Column(db.Integer, default=0, doc='关注的人数')
    fans_count = db.Column(db.Integer, default=0, doc='被关注的人数（粉丝数）')
    like_count = db.Column(db.Integer, default=0, doc='累计点赞人数')
    read_count = db.Column(db.Integer, default=0, doc='累计阅读人数')


class UserProfile(db.Model):
    """
    用户资料表
    """
    __tablename__ = 'user_profile'

    class GENDER:
        MALE = 0
        FEMALE = 1

    user_id = db.Column(db.Integer, primary_key=True, doc='用户ID')
    gender = db.Column(db.Integer, default=0, doc='性别')
    birthday = db.Column(db.Date, doc='生日')
    real_name = db.Column(db.String, doc='真实姓名')
    id_card = db.Column(db.String, doc='身份证号')
    introduction = db.Column(db.String, doc='个人简介')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')
    register_media_time = db.Column(db.DateTime, doc='注册自媒体时间')


class Follow(db.Model):
    """
    用户关注表
    """
    __tablename__ = 'user_follow'

    follow_id = db.Column(db.Integer, primary_key=True, doc='主键ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    following_user_id = db.Column(db.Integer, doc='关注的用户ID')
    is_deleted = db.Column(db.Boolean, default=False, doc='是否取消关注')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class Blacklist(db.Model):
    """
    用户拉黑表
    """
    __tablename__ = 'user_blacklist'

    blacklist_id = db.Column(db.Integer, primary_key=True, doc='主键ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    blacklist_user_id = db.Column(db.Integer, doc='拉黑的用户ID')
    is_deleted = db.Column(db.Boolean, default=False, doc='是否取消拉黑')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class Search(db.Model):
    """
    用户搜索记录表
    """
    __tablename__ = 'user_search'

    search_id = db.Column(db.Integer, primary_key=True, doc='主键ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    keyword = db.Column(db.String, doc='关键词')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    is_deleted = db.Column(db.Boolean, default=False, doc='是否删除')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class Material(db.Model):
    """
    素材表
    """
    __tablename__ = 'user_material'

    class TYPE:
        IMAGE = 0
        VIDEO = 1
        AUDIO = 2

    class STATUS:
        UNREVIEWED = 0  # 待审核
        APPROVED = 1  # 审核通过
        FAILED = 2  # 审核失败
        DELETED = 3  # 已删除

    material_id = db.Column(db.Integer, primary_key=True, doc='素材ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    type = db.Column(db.Integer, default=0, doc='素材类型')
    hash = db.Column(db.String, doc='素材指纹')
    url = db.Column(db.String, doc='素材链接地址')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    status = db.Column(db.Integer, default=0, doc='状态')
    reviewer_id = db.Column(db.Integer, doc='审核人员ID')
    review_time = db.Column(db.DateTime, doc='审核时间')
    is_collected = db.Column(db.Boolean, default=False, doc='是否收藏')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')






