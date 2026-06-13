from celery import Celery

from app.backend.config import backend_settings

REDIS_URL = backend_settings.redis_url

celery_app = Celery("ai_hedge_fund", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
