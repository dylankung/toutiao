from flask import current_app
import time
from sqlalchemy.orm import load_only
from sqlalchemy import func
from flask_restful import marshal, fields
import json
from redis.exceptions import RedisError, ConnectionError
from sqlalchemy.exc import SQLAlchemyError

from models.user import User, Relation, UserProfile
from models.news import Article
from models import db
from . import constants


class UserProfileCache(object):
    """
    用户信息缓存
    """
    user_fields_for_db = {
        'mobile': fields.String(attribute='mobile'),
        'name': fields.String(attribute='name'),
        'photo': fields.String(attribute='profile_photo'),
        'is_media': fields.Integer(attribute='is_media'),
        'intro': fields.String(attribute='introduction'),
        'certi': fields.String(attribute='certificate'),
        'art_count': fields.Integer(attribute='article_count'),
        'follow_count': fields.Integer(attribute='following_count'),
        'fans_count': fields.Integer(attribute='fans_count'),
        'like_count': fields.Integer(attribute='like_count'),
        'read_count': fields.Integer(attribute='read_count'),
    }

    def __init__(self, user_id):
        self.key = 'user:{}:profile'.format(user_id)
        self.user_id = user_id

    def _generate_user_profile_cache(self, user=None):
        """
        从数据库查询用户数据
        :param user: 已存在的用户数据
        :return:
        """
        if user is None:
            user = User.query.options(load_only(User.name,
                                                User.mobile,
                                                User.profile_photo,
                                                User.is_media,
                                                User.introduction,
                                                User.certificate,
                                                User.article_count,
                                                User.following_count,
                                                User.fans_count,
                                                User.like_count,
                                                User.read_count)) \
                .filter_by(id=self.user_id).first()
        user.profile_photo = user.profile_photo or ''
        user.introduction = user.introduction or ''
        user.certificate = user.certificate or ''
        user_data = marshal(user, self.user_fields_for_db)
        return user_data

    def save(self, user=None, force=False):
        """
        设置用户数据缓存
        """
        rc = current_app.redis_cluster

        if force:
            exists = False
        else:
            try:
                exists = rc.hexists(self.key, 'mobile')
            except RedisError as e:
                current_app.logger.error(e)
                exists = False

        if not exists:
            # This user cache data did not exist previously.
            user_data = self._generate_user_profile_cache(user)

            # 补充exists字段，为防止缓存击穿使用
            # 参考下面determine_user_exists方法说明
            user_data['exists'] = 1

            try:
                pl = rc.pipeline()
                pl.hmset(self.key, user_data)
                pl.expire(self.key, constants.UserProfileCacheTTL.get_val())
                results = pl.execute()
            except RedisError as e:
                current_app.logger.error(e)
            else:
                # 有效期设置失败
                if results[0] and not results[1]:
                    rc.delete(self.key)

            return user_data

    def get(self):
        """
        获取用户数据
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.hgetall(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None
        if ret:
            # hit cache
            user_data = {
                    'mobile': ret[b'mobile'].decode(),
                    'name': ret[b'name'].decode(),
                    'photo': ret[b'photo'].decode(),
                    'is_media': int(ret[b'is_media']),
                    'intro': ret[b'intro'].decode(),
                    'certi': ret[b'certi'].decode(),
                    'art_count': int(ret[b'art_count']),
                    'follow_count': int(ret[b'follow_count']),
                    'fans_count': int(ret[b'fans_count']),
                    'like_count': int(ret[b'like_count']),
                    'read_count': int(ret[b'read_count']),
                }
        else:
            user_data = self.save(force=True)

        if not user_data['photo']:
            user_data['photo'] = constants.DEFAULT_USER_PROFILE_PHOTO
        user_data['photo'] = current_app.config['QINIU_DOMAIN'] + user_data['photo']
        return user_data

    def update(self, profile):
        """
        更新用户资料
        :param profile: dict
        :return:
        """
        rc = current_app.redis_cluster

        # 此处使用ttl是看还有多长时间过期，如果有效期剩余过小，更新无意义
        try:
            ttl = rc.ttl(self.key)
            if ttl > constants.ALLOW_UPDATE_USER_PROFILE_CACHE_TTL_LIMIT:
                rc.hmset(self.key, profile)
        except RedisError as e:
            current_app.logger.error(e)

    def exists(self):
        """
        判断用户是否存在
        :return: bool
        """
        rc = current_app.redis_cluster

        # 此处可使用的键有三种选择 user:{}:profile 或 user:{}:status 或 新建
        # status主要为当前登录用户，而profile不仅仅是登录用户，覆盖范围更大，所以使用profile
        try:
            exists = rc.hget(self.key, 'exists')
        except RedisError as e:
            current_app.logger.error(e)
            exists = None

        if exists is not None:
            exists = int(exists)

        if exists == 1:
            return True
        elif exists == 0:
            return False
        else:
            # 缓存中未查到
            ret = db.session.query(func.count(User.id)).filter_by(id=self.user_id).first()
            if ret[0] > 0:
                try:
                    self.save()
                except SQLAlchemyError as e:
                    current_app.logger.error(e)
            else:
                try:
                    pl = rc.pipeline()
                    pl.hset(self.key, 'exists', 0)
                    pl.expire(self.key, constants.UserNotExistsCacheTTL.get_val())
                    results = pl.execute()
                    if results[0] and not results[1]:
                        pl.delete(self.key)
                except RedisError as e:
                    current_app.logger.error(e)
            return bool(ret[0])

    def update_follow_count(self, increment):
        """
        更新关注数
        :param increment:
        :return:
        """
        rc = current_app.redis_cluster
        try:
            ttl = rc.ttl(self.key)
            if ttl > constants.ALLOW_UPDATE_USER_PROFILE_STATISTIC_CACHE_TTL_LIMIT:
                rc.hincrby(self.key, 'follow_count', increment)
        except RedisError as e:
            current_app.logger.error(e)

    def get_follow_count(self):
        """
        获取关注数
        :return:
        """
        rc = current_app.redis_cluster
        try:
            ret = rc.hget(self.key, 'follow_count')
        except RedisError as e:
            current_app.logger.error(e)
            ret = None
        if ret is not None:
            ret = int(ret)
        return ret

    def update_fans_count(self, increment):
        """
        更新粉丝数
        :param increment:
        :return:
        """
        rc = current_app.redis_cluster
        try:
            ttl = rc.ttl(self.key)
            if ttl > constants.ALLOW_UPDATE_USER_PROFILE_STATISTIC_CACHE_TTL_LIMIT:
                rc.hincrby(self.key, 'fans_count', increment)
        except RedisError as e:
            current_app.logger.error(e)

    def get_fans_count(self):
        """
        获取粉丝数
        """
        rc = current_app.redis_cluster
        try:
            ret = rc.hget(self.key, 'fans_count')
        except RedisError as e:
            current_app.logger.error(e)
            ret = None
        if ret is not None:
            ret = int(ret)
        return ret


class UserStatusCache(object):
    """
    用户状态缓存
    """
    def __init__(self, user_id):
        self.key = 'user:{}:status'.format(user_id)
        self.user_id = user_id

    def save(self, status):
        """
        设置用户状态缓存
        :param status:
        """
        try:
            current_app.redis_cluster.setex(self.key, constants.UserStatusCacheTTL.get_val(), status)
        except RedisError as e:
            current_app.logger.error(e)

    def get(self):
        """
        获取用户状态
        :return:
        """
        rc = current_app.redis_cluster

        try:
            status = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            status = None

        if status is not None:
            return status
        else:
            user = User.query.options(load_only(User.status)).filter_by(id=self.user_id).first()
            if user:
                self.save(user.status)
                return user.status
            else:
                return False


class UserAdditionalProfileCache(object):
    """
    用户附加资料缓存（如性别、生日等）
    """
    def __init__(self, user_id):
        self.key = 'user:{}:profilex'.format(user_id)
        self.user_id = user_id

    def get(self):
        """
        获取用户的附加资料（如性别、生日等）
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            return json.loads(ret)
        else:
            profile = UserProfile.query.options(load_only(UserProfile.gender, UserProfile.birthday)) \
                .filter_by(id=self.user_id).first()
            profile_dict = {
                'gender': profile.gender,
                'birthday': profile.birthday.strftime('%Y-%m-%d') if profile.birthday else ''
            }
            try:
                rc.setex(self.key, constants.UserAdditionalProfileCacheTTL.get_val(), json.dumps(profile_dict))
            except RedisError as e:
                current_app.logger.error(e)
            return profile_dict

    def clear(self):
        """
        清除用户的附加资料
        :return:
        """
        try:
            current_app.redis_cluster.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)


class UserFollowingCache(object):
    """
    用户关注缓存数据
    """
    def __init__(self, user_id):
        self.key = 'user:{}:following'.format(user_id)
        self.user_id = user_id

    def get(self):
        """
        获取用户的关注列表
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.zrevrange(self.key, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # In order to be consistent with db data type.
            return [int(uid) for uid in ret]

        # 为了防止缓存击穿，先尝试从缓存中判断关注数是否为0，若为0不再查询数据库
        ret = UserProfileCache(self.user_id).get_follow_count()
        if ret == 0:
            return []

        ret = Relation.query.options(load_only(Relation.target_user_id, Relation.utime)) \
            .filter_by(user_id=self.user_id, relation=Relation.RELATION.FOLLOW) \
            .order_by(Relation.utime.desc()).all()

        followings = []
        cache = []
        for relation in ret:
            followings.append(relation.target_user_id)
            cache.append(relation.utime.timestamp())
            cache.append(relation.target_user_id)

        if cache:
            try:
                pl = rc.pipeline()
                pl.zadd(self.key, *cache)
                pl.expire(self.key, constants.UserFollowingsCacheTTL.get_val())
                results = pl.execute()
                if results[0] and not results[1]:
                    rc.delete(self.key)
            except RedisError as e:
                current_app.logger.error(e)

        return followings

    def determine_follows_target(self, target_user_id):
        """
        判断用户是否关注了目标用户
        :param target_user_id: 被关注的用户id
        :return:
        """
        followings = self.get()

        return int(target_user_id) in followings

    def update(self, target_user_id, timestamp, increment=1):
        """
        更新用户的关注缓存数据
        :param target_user_id: 被关注的目标用户
        :param timestamp: 关注时间戳
        :param increment: 增量
        :return:
        """
        rc = current_app.redis_cluster

        # Update user following count
        UserProfileCache(self.user_id).update_follow_count(increment)

        # Update user following user id list
        try:
            ttl = rc.ttl(self.key)
            if ttl > constants.ALLOW_UPDATE_FOLLOW_CACHE_TTL_LIMIT:
                if increment > 0:
                    rc.zadd(self.key, timestamp, target_user_id)
                else:
                    rc.zrem(self.key, target_user_id)
        except RedisError as e:
            current_app.logger.error(e)

        # Update target user followers(fans) count
        UserProfileCache(target_user_id).update_fans_count(increment)

        # Update target user followers(fans) user id list
        UserFollowersCache(target_user_id).update(self.user_id, timestamp, increment)


class UserFollowersCache(object):
    """
    用户粉丝缓存
    """
    def __init__(self, user_id):
        self.key = 'user:{}:fans'.format(user_id)
        self.user_id = user_id

    def get(self):
        """
        获取用户的粉丝列表
        :return:
        """
        rc = current_app.redis_cluster

        try:
            ret = rc.zrevrange(self.key, 0, -1)
        except RedisError as e:
            current_app.logger.error(e)
            ret = None

        if ret:
            # In order to be consistent with db data type.
            return [int(uid) for uid in ret]

        ret = UserProfileCache(self.user_id).get_fans_count()
        if ret == 0:
            return []

        ret = Relation.query.options(load_only(Relation.user_id, Relation.utime))\
            .filter_by(target_user_id=self.user_id, relation=Relation.RELATION.FOLLOW)\
            .order_by(Relation.utime.desc()).all()

        followers = []
        cache = []
        for relation in ret:
            followers.append(relation.user_id)
            cache.append(relation.utime.timestamp())
            cache.append(relation.user_id)

        if cache:
            try:
                pl = rc.pipeline()
                pl.zadd(self.key, *cache)
                pl.expire(self.key, constants.UserFansCacheTTL.get_val())
                results = pl.execute()
                if results[0] and not results[1]:
                    rc.delete(self.key)
            except RedisError as e:
                current_app.logger.error(e)

        return followers

    def update(self, target_user_id, timestamp, increment=1):
        """
        更新粉丝数缓存
        """
        rc = current_app.redis_cluster
        try:
            ttl = rc.ttl(self.key)
            if ttl > constants.ALLOW_UPDATE_FOLLOW_CACHE_TTL_LIMIT:
                if increment > 0:
                    rc.zadd(self.key, timestamp, target_user_id)
                else:
                    rc.zrem(self.key, target_user_id)
        except RedisError as e:
            current_app.logger.error(e)


class UserReadingHistoryStorage(object):
    """
    用户阅读历史
    """
    def __init__(self, user_id):
        self.key = 'user:{}:his'.format(user_id)
        self.user_id = user_id

    def save(self, article_id):
        """
        保存用户阅读历史
        :param article_id: 文章id
        :return:
        """
        try:
            pl = current_app.redis_master.pipeline()
            pl.zadd(self.key, time.time(), article_id)
            pl.zremrangebyrank(self.key, 0, -1*(constants.READING_HISTORY_COUNT_PER_USER+1))
            pl.execute()
        except RedisError as e:
            current_app.logger.error(e)

    def get(self, page, per_page):
        """
        获取阅读历史
        """
        r = current_app.redis_master
        try:
            total_count = r.zcard(self.key)
        except ConnectionError as e:
            r = current_app.redis_slave
            total_count = r.zcard(self.key)

        article_ids = []
        if total_count > 0 and (page - 1) * per_page < total_count:
            try:
                article_ids = r.zrevrange(self.key, (page - 1) * per_page, page * per_page - 1)
            except ConnectionError as e:
                current_app.logger.error(e)
                article_ids = current_app.redis_slave.zrevrange(self.key, (page - 1) * per_page, page * per_page - 1)

        return total_count, article_ids


def get_user_articles(user_id):
    """
    获取用户的所有文章列表
    :param user_id:
    :return:
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()

    ret = r.zrevrange('user:{}:art'.format(user_id), 0, -1)
    if ret:
        r.zadd('user:art', timestamp, user_id)
        return [int(aid) for aid in ret]

    ret = r.hget('user:{}'.format(user_id), 'art_count')
    if ret is not None and int(ret) == 0:
        return []

    ret = Article.query.options(load_only(Article.id, Article.ctime))\
        .filter_by(user_id=user_id, status=Article.STATUS.APPROVED)\
        .order_by(Article.ctime.desc()).all()

    articles = []
    cache = []
    for article in ret:
        articles.append(article.id)
        cache.append(article.ctime.timestamp())
        cache.append(article.id)

    if cache:
        pl = r.pipeline()
        pl.zadd('user:art', timestamp, user_id)
        pl.zadd('user:{}:art'.format(user_id), *cache)
        pl.execute()

    return articles


def get_user_articles_by_page(user_id, page, per_page):
    """
    获取用户的文章列表
    :param user_id:
    :param page: 页数
    :param per_page: 每页数量
    :return: total_count, [article_id, ..]
    """
    r = current_app.redis_cli['user_cache']
    timestamp = time.time()

    key = 'user:{}:art'.format(user_id)
    exist = r.exists(key)
    if exist:
        # Cache exists.
        r.zadd('user:art', timestamp, user_id)
        total_count = r.zcard(key)
        ret = r.zrevrange(key, (page - 1) * per_page, page * per_page)
        if ret:
            return total_count, [int(aid) for aid in ret]
        else:
            return total_count, []
    else:
        # No cache.
        ret = r.hget('user:{}'.format(user_id), 'art_count')
        if ret is not None and int(ret) == 0:
            return 0, []

        ret = Article.query.options(load_only(Article.id, Article.ctime)) \
            .filter_by(user_id=user_id, status=Article.STATUS.APPROVED) \
            .order_by(Article.ctime.desc()).all()

        articles = []
        cache = []
        for article in ret:
            articles.append(article.id)
            cache.append(article.ctime.timestamp())
            cache.append(article.id)

        if cache:
            pl = r.pipeline()
            pl.zadd('user:art', timestamp, user_id)
            pl.zadd(key, *cache)
            pl.execute()

        total_count = len(articles)
        page_articles = articles[(page - 1) * per_page:page * per_page]

        return total_count, page_articles


# 已废弃
# def synchronize_reading_history_to_db(user_id):
#     """
#     同步用户的阅读历史到数据库
#     :param user_id:
#     :return:
#     """
#     r = current_app.redis_cli['read_his']
#     history = r.hgetall('his:{}'.format(user_id))
#     if not history:
#         return
#
#     pl = r.pipeline()
#     pl.srem('users', user_id)
#     pl.delete('his:{}'.format(user_id))
#     pl.execute()
#
#     sql = ''
#     for article_id, timestamp in history.items():
#         read_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timestamp)))
#         sql += "INSERT INTO news_read (user_id, article_id, create_time, update_time) VALUES({}, {}, '{}', '{}')" \
#                " ON DUPLICATE KEY UPDATE update_time ='{}';".format(
#                     user_id, article_id, read_time, read_time, read_time
#                )
#
#     if sql:
#         db.session.execute(sql)
#         db.session.commit()


def update_user_article_read_count(user_id):
    """
    更新用户文章被阅读数
    :param user_id:
    :return:
    """
    User.query.filter_by(id=user_id).update({'read_count': User.read_count + 1})
    db.session.commit()

    r = current_app.redis_cli['user_cache']
    key = 'user:{}'.format(user_id)
    exist = r.exists(key)

    if exist:
        r.hincrby(key, 'read_count', 1)


