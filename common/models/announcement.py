from . import db


class Announcement(db.Model):
    """
    系统公告表
    """
    __tablename__ = 'global_announcement'

    class STATUS:
        UNPUBLISHED = 0  # 待发布
        PUBLISHED = 1  # 已发布
        OBSELETE = 2  # 已撤下

    announcement_id = db.Column(db.Integer, primary_key=True, doc='公告ID')
    title = db.Column(db.String, doc='标题')
    content = db.Column(db.Text, doc='正文')
    create_time = db.Column(db.DateTime, doc='创建时间')
    status = db.Column(db.Integer, doc='状态')
    publish_time = db.Column(db.DateTime, doc='发布时间')
    update_time = db.Column(db.DateTime, doc='更新时间')
