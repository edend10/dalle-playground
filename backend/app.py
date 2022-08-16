print("--> Starting DALL-E Script")

import yaml
import argparse
import os
from pathlib import Path
import time

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from consts import DEFAULT_IMG_OUTPUT_DIR
from utils import parse_arg_boolean, parse_arg_dalle_version
from consts import ModelSize

from celery import Celery
celery_app = Celery('redis://redis:6379/0') ## TODO: parameterize

app = Flask(__name__)
CORS(app)
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

    task_id = celery_app.send_task("create_task_generate", (text_prompt, num_images))

    generated_images = []	

    returned_generated_images = []
    
    print(f"Created {num_images} images from text prompt [{text_prompt}]")
    
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
    print("got request:", json_data)
    b64_images = json_data["b64_images"]

    return f"got {len(b64_images)} images"
	

#with app.app_context():
#    print(f"--> Loading model - DALL-E {model_version}")
#    dalle_model = DalleModel(model_version)
#    dalle_model.generate_images("warm-up", 1)
#    print(f"--> Model loaded - DALL-E {model_version}")
#    
#    print(f"--> Loading models - glid")
#    glid_params = glid.load_models(steps=100, skip_rate=0.6)
#    print(f"--> Models loaded - glid")
#    
#    print(f"--> Loading model - swinir")
#    swinir_model = swinir.load_model(is_real_sr=True)
#    print(f"--> Model loaded - swinir")
#    
#    print("--> DALL-E Server is up and running!")


if __name__ == "__main__":
    print("flask main")
    app.run(host="0.0.0.0", port=port, debug=False)
