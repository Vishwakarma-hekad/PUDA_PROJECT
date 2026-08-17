from celery import Celery
from Backend.config import settings
celery= Celery("puda",broker=settings.CELERY_BROKER_URL,
               backend=settings.CELERY_RESULT_BACKEND)

celery.conf.imports = (
    "Backend.tasks.drawing_task",
)