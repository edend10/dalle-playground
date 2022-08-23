## Adapted from: https://testdriven.io/blog/flask-and-celery/
from torch import autocast
from diffusers import StableDiffusionPipeline

import os
import time
import yaml
import base64
import json
from io import BytesIO
import requests

from celery import Celery
from celery.signals import worker_init

from flask_socketio import SocketIO, emit

celery_backend_url = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379"),
celery_broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
app_backend_url = os.environ.get("APP_BACKEND_URL", "http://localhost:8080")

TASK_COMPLETE_URL = f"{app_backend_url}/internal/generate-task-complete"

celery = Celery(
	__name__,
    backend=celery_backend_url,
    broker=celery_broker_url
)

socketio = SocketIO(message_queue=celery_broker_url)

## Adapted from https://towardsdatascience.com/serving-deep-learning-algorithms-as-a-service-6aa610368fde
celery.conf.update({
#    'imports': (
#        'api.celery_jobs_app.tasks.tasks'
#    ),
#    'task_routes': {
#        'calculate-image-task': {'queue': 'images-queue'}
#        }
#    },
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'worker_prefetch_multiplier': 1,
    'task_acks_late': True,
    'task_track_started': True,
    'result_expires': 604800,  # one week
    'task_reject_on_worker_lost': True,
    'task_queue_max_priority': 10
})

## load model config
with open("celery_config.yaml") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.FullLoader)

## declare global empty model variables
dalle_model = None

def load_dalle_model(model_version):
	os.environ["TOKENIZERS_PARALLELISM"] = "false"

	print(f"--> Loading model - DALL-E {model_version}")
	dalle_model = StableDiffusionPipeline.from_pretrained(
        "CompVis/stable-diffusion-v1-4", 
        use_auth_token="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"
    ).to("cuda")

	print(f"--> Model loaded - DALL-E {model_version}")

	return dalle_model

dalle_model = load_dalle_model(config["model_version"])

#@worker_init.connect()
#def on_worker_init(**_):
#    global dalle_model
#    dalle_model = load_dalle_model(config["model_version"])

## TODO: load model and predict
## example: https://stackoverflow.com/questions/52098967/python-redis-queue-rq-how-to-avoid-preloading-ml-model-for-each-job
@celery.task(name="create_task_generate")
def create_task_generate(prompt, num_images, room_id):
#    global dalle_model

    print(f"Predicting DALL-E for prompt: '{prompt}'")
    with autocast("cuda"):
        generated_images = [dalle_model(prompt)["sample"][0]]
    print("created image!!!")

#    diffused_images = []
#    for img in generated_images:
#        results = glid.do_run(*glid_params, init_image=img, text=prompt, num_batches=1, batch_size=1)
#        for batch in results:
#            for diffused_img in batch:
#                diffused_images.append(diffused_img)
#
#    upscaled_images = []
#    for img in diffused_images:
#        upscaled_img = swinir.do_run(swinir_model, img, is_real_sr=True)
#        
#        upscaled_images.append(upscaled_img)
# 	 generated_images = generated_images + diffused_images + upscaled_images
#        

    encoded_images = []
    for idx, img in enumerate(generated_images):
        buffered = BytesIO()
        img.save(buffered, format=config["img_format"])
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        encoded_images.append(img_str)

    data = {"b64_images": encoded_images, "image_format": config["img_format"], "room_id": room_id}
    serialized_data = json.dumps(data)
    socketio.emit("generate_complete", {"data": {"b64_images": encoded_images, "image_format": config["img_format"]}}, namespace="/", to=room_id)

#    try:
#        response = requests.post(url=TASK_COMPLETE_URL, data=serialized_data)
#
#        if response.status_code == 200:
#            print("Successfully notified task complete (200)")
#        else:
#            print(f"Failed to notify task complete (url: {TASK_COMPLETE_URL}, code: {response.status_code}): '{response.content}'")
#            return False
#
#    except Exception as e:
#        print(f"Request to notify task complete failed with exception (url: {TASK_COMPLETE_URL}): {str(e)}'")
#        return False

    return True
