#! /bin/bash
source ~/.bashrc
export PYTHONPATH=/root/config:$PYTHONPATH
export FLASK_ENV=production
export TOUTIAO_WEB_SETTINGS=/root/config/web_deploy.py
export TOUTIAO_CELERY_SETTINGS=celery_deploy.CeleryConfig
cd /root/toutiao-backend/
workon toutiao
exec gunicorn -b 0.0.0.0:8003 --access-logfile /root/logs/access_mis.log --error-logfile /root/logs/error_mis.log --access-logformat '"%({X-Real-IP}i)s" %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' mis.main:app