from celery import Celery

celery= Celery("puda",broker="redis://localhost:6379/0",
               backend="redis://localhost:6379/1")

celery.conf.imports = (
    "tasks.drawing_task",
)