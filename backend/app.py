print("--> Starting DALL-E Script")

import yaml
import argparse
import os
from pathlib import Path
import time

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, emit, join_room
from consts import DEFAULT_IMG_OUTPUT_DIR
from utils import parse_arg_boolean, parse_arg_dalle_version
from consts import ModelSize

from celery import Celery
celery_app = Celery('redis://redis:6379/0') ## TODO: parameterize

app = Flask(__name__)
## TODO: from env
frontend_ip = "35.184.104.157"

frontend_url = f"http://{frontend_ip}:3000"
CORS(app, origins=[frontend_url])
socketio = SocketIO(app, cors_allowed_origins=[frontend_url], engineio_logger=True)
print("--> Starting DALL-E Server. This might take up to two minutes.")

with open("app_config.yaml") as yamlfile:
    app_config = yaml.load(yamlfile, Loader=yaml.FullLoader)
    port = int(app_config["port"])
    output_dir = app_config["output_dir"]

@app.route("/dalle", methods=["POST"])
@cross_origin()
def generate_images_api():
    json_data = request.get_json(force=True)
    text_prompt = json_data["text"]
    num_images = json_data["num_images"]
    room_id = json_data["room_id"]

    task_id = celery_app.send_task("create_task_generate", (text_prompt, num_images, room_id))

    generated_images = []	

    returned_generated_images = []
    
    print(f"Submitted task for {num_images} images from text prompt [{text_prompt}]")
    
    response = {'generatedImgs': returned_generated_images,
    'generatedImgsFormat': "bla"}
    return jsonify(response)


@app.route("/", methods=["GET"])
@cross_origin()
def health_check():
    return jsonify(success=True)

@app.route("/internal/generate-task-complete", methods=["POST"])
def generate_task_complete():
    json_data = request.get_json(force=True)
    print("got request:", {k: [x[:30] for x in v] if type(v) == list else v for k,v in json_data.items()})
    b64_images = json_data["b64_images"]
    image_format = json_data["image_format"]
    room_id = json_data["room_id"]

    emit("generate_complete", {"data": {"b64_images": b64_images, "image_format": image_format}}, namespace="/", room=room_id)
    print(f"emitted event for room_id: {room_id}")

    return f"got {len(b64_images)} images"

### SocketIO
@socketio.on("connect")
def socket_connect():
    emit('after connect', {'data': 'Connected'})

@socketio.on("disconnect")
def socket_disconnect():
    emit('after disconnect', {'data': 'Disconnected'})

@socketio.on("generate_complete")
def socket_generate_complete():
    print("generate_complete emitted")


if __name__ == "__main__":
    print("flask main")
    socketio.run(host="0.0.0.0", port=port, debug=False)
