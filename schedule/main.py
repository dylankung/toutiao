import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor

from common import create_logger


# 创建scheduler，多进程执行
executors = {
    'default': ProcessPoolExecutor(3)
}

scheduler = BlockingScheduler(executors=executors)

create_logger()

# 添加离线任务
from reading_history import save_reading_history_to_mysql
scheduler.add_job(save_reading_history_to_mysql, trigger='interval', minutes=30)

from clear_cache import clear_user_cache, clear_comment_cache
scheduler.add_job(clear_user_cache, trigger='interval', minutes=10)
scheduler.add_job(clear_comment_cache, trigger='interval', minutes=10)

# from cover import generate_article_cover
# scheduler.add_job(generate_article_cover, trigger='interval', years=1)

scheduler.start()


