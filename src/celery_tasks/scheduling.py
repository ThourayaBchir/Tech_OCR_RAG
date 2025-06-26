import logging

from celery import Celery

from utils.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery("pipeline", broker=settings.CELERY_BROKER_URL)
celery_app.conf.task_always_eager = True


from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "schedule-ocr-every-30min": {
        "task": "ingest.schedule_ocr",
        "schedule": crontab(minute="*/30"),
    },
}


# from celery.signals import worker_ready


# @worker_ready.connect
# def at_start(sender, **kwargs):
#     with sender.app.connection() as conn:
#         sender.app.send_task("ingest.schedule_ocr")
