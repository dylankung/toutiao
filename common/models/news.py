from datetime import datetime

from . import db


class Channel(db.Model):
    """
    新闻频道
    """
    __tablename__ = 'news_channel'

    channel_id = db.Column(db.Integer, primary_key=True, doc='频道ID')
    channel_name = db.Column(db.String, doc='频道名称')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class UserChannel(db.Model):
    """
    用户关注频道表
    """
    __tablename__ = 'news_user_channel'

    user_channel_id = db.Column(db.Integer, primary_key=True, doc='主键ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    channel_id = db.Column(db.Integer, doc='频道ID')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    is_deleted = db.Column(db.Boolean, default=False, doc='是否删除')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class PostBasic(db.Model):
    """
    帖文基本信息表
    """
    __tablename__ = 'news_post_basic'

    class STATUS:
        DRAFT = 0  # 草稿
        UNREVIEWED = 1  # 待审核
        APPROVED = 2  # 审核通过
        FAILED = 3  # 审核失败
        DELETED = 4  # 已删除

    post_id = db.Column(db.Integer, primary_key=True, doc='帖文ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    channel_id = db.Column(db.Integer, doc='频道ID')
    title = db.Column(db.String, doc='标题')
    cover = db.Column(db.JSON, doc='封面')
    is_advertising = db.Column(db.Boolean, default=False, doc='是否投放广告')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    status = db.Column(db.Integer, default=0, doc='帖文状态')
    reviewer_id = db.Column(db.Integer, doc='审核人员ID')
    review_time = db.Column(db.DateTime, doc='审核时间')
    delete_time = db.Column(db.DateTime, doc='删除时间')
    comment_count = db.Column(db.Integer, default=0, doc='评论数')


class PostContent(db.Model):
    """
    帖文内容表
    """
    __tablename__ = 'news_post_content'

    post_id = db.Column(db.Integer, primary_key=True, doc='帖文ID')
    content = db.Column(db.Text, doc='帖文内容')


class PostStatistic(db.Model):
    """
    帖文统计表
    """
    __tablename__ = 'news_post_statistic'

    post_id = db.Column(db.Integer, primary_key=True, doc='帖文ID')
    read_count = db.Column(db.Integer, default=0, doc='阅读量')
    like_count = db.Column(db.Integer, default=0, doc='点赞量')
    dislisk_count = db.Column(db.Integer, default=0, doc='不喜欢数')
    repost_count = db.Column(db.Integer, default=0, doc='转发数')
    collect_count = db.Column(db.Integer, default=0, doc='收藏数')


class Collection(db.Model):
    """
    用户收藏表
    """
    __tablename__ = 'news_collection'

    collection_id = db.Column(db.Integer, primary_key=True, doc='主键ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    post_id = db.Column(db.Integer, doc='帖文ID')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
    is_deleted = db.Column(db.Boolean, default=False, doc='是否删除')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


class Read(db.Model):
    """
    用户阅读历史表
    """
    __tablename__ = 'news_read'

    read_id = db.Column(db.Integer, primary_key=True, doc='主键ID')
    user_id = db.Column(db.Integer, doc='用户ID')
    post_id = db.Column(db.Integer, doc='帖文ID')
    create_time = db.Column(db.DateTime, default=datetime.now, doc='创建时间')
