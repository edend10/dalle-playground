## Adapted from: https://testdriven.io/blog/flask-and-celery/

import os
import time
import yaml

from celery import Celery
from celery.signals import worker_init

from dalle_model import DalleModel


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

## load model config
with open("model_config.yaml") as yamlfile:
    model_config = yaml.load(yamlfile, Loader=yaml.FullLoader)

## declare global empty model variables
dalle_model = None

def load_dalle_model(model_version):
    print(f"--> Loading model - DALL-E {model_version}")
    dalle_model = DalleModel(model_version)
    print(f"--> Model loaded - DALL-E {model_version}")
    print("--> Generating warmup images for DALL-E")
    dalle_model.generate_images("warm-up", 1)

@worker_init.connect()
def on_worker_init(**_):
    global dalle_model
    dalle_model = load_dalle_model(model_config["model_version"])

## TODO: load model and predict
## example: https://stackoverflow.com/questions/52098967/python-redis-queue-rq-how-to-avoid-preloading-ml-model-for-each-job
@celery.task(name="create_dalle_task")
def create_dalle_task(prompt, num_images):
    print(f"Predicting DALL-E for prompt: '{prompt}'")

    return True
