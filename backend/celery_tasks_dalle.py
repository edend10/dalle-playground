## Adapted from: https://testdriven.io/blog/flask-and-celery/

import os
import time

from celery import Celery


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

## TODO: load model and predict
## example: https://stackoverflow.com/questions/52098967/python-redis-queue-rq-how-to-avoid-preloading-ml-model-for-each-job
@celery.task(name="create_dalle_task")
def create_task(prompt, num_images):
    print(f"Predicting DALL-E for prompt: '{prompt}'")


    return True
