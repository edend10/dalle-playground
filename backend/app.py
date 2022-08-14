print("--> Starting DALL-E Script")

import yaml
import argparse
import base64
import os
from pathlib import Path
from io import BytesIO
import time

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from consts import DEFAULT_IMG_OUTPUT_DIR
from utils import parse_arg_boolean, parse_arg_dalle_version
from consts import ModelSize

import glid
import swinir

app = Flask(__name__)
CORS(app)
print("--> Starting DALL-E Server. This might take up to two minutes.")

from dalle_model import DalleModel
dalle_model = None

#parser = argparse.ArgumentParser(description = "A DALL-E app to turn your textual prompts into visionary delights")
#parser.add_argument("--port", type=int, default=8000, help = "backend port")
#parser.add_argument("--model_version", type = parse_arg_dalle_version, default = ModelSize.MINI, help = "Mini, Mega, or Mega_full")
#parser.add_argument("--save_to_disk", type = parse_arg_boolean, default = False, help = "Should save generated images to disk")
#parser.add_argument("--img_format", type = str.lower, default = "JPEG", help = "Generated images format", choices=['jpeg', 'png'])
#parser.add_argument("--output_dir", type = str, default = DEFAULT_IMG_OUTPUT_DIR, help = "Customer directory for generated images")
#args = parser.parse_args()

with open("app_config.yaml") as yamlfile:
    app_config = yaml.load(yamlfile, Loader=yaml.FullLoader)
    port = int(app_config["port"])
    save_to_disk = bool(app_config["save_to_disk"])
    img_format = app_config["img_format"]
    output_dir = app_config["output_dir"]

with open("model_config.yaml") as yamlfile:
    model_config = yaml.load(yamlfile, Loader=yaml.FullLoader)
    model_version = model_config["model_version"]


@app.route("/dalle", methods=["POST"])
@cross_origin()
def generate_images_api():
    json_data = request.get_json(force=True)
    text_prompt = json_data["text"]
    num_images = json_data["num_images"]
    generated_images = dalle_model.generate_images(text_prompt, num_images)

    diffused_images = []
    for img in generated_images:
        results = glid.do_run(*glid_params, init_image=img, text=text_prompt, num_batches=1, batch_size=1)
        for batch in results:
            for diffused_img in batch:
                diffused_images.append(diffused_img)

    upscaled_images = []
    for img in diffused_images:
        upscaled_img = swinir.do_run(swinir_model, img, is_real_sr=True)
        
        upscaled_images.append(upscaled_img)
        

    returned_generated_images = []
    if save_to_disk: 
        dir_name = os.path.join(output_dir,f"{time.strftime('%Y-%m-%d_%H-%M-%S')}_{text_prompt}")
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    for idx, img in enumerate(generated_images + diffused_images + upscaled_images):
        if save_to_disk: 
          img.save(os.path.join(dir_name, f'{idx}.{img_format}'), format=img_format)

        buffered = BytesIO()
        img.save(buffered, format=img_format)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        returned_generated_images.append(img_str)

    print(f"Created {num_images} images from text prompt [{text_prompt}]")
    
    response = {'generatedImgs': returned_generated_images,
    'generatedImgsFormat': img_format}
    return jsonify(response)


@app.route("/", methods=["GET"])
@cross_origin()
def health_check():
    return jsonify(success=True)

with app.app_context():
    print(f"--> Loading model - DALL-E {model_version}")
    dalle_model = DalleModel(model_version)
    dalle_model.generate_images("warm-up", 1)
    print(f"--> Model loaded - DALL-E {model_version}")
    
    print(f"--> Loading models - glid")
    glid_params = glid.load_models(steps=100, skip_rate=0.6)
    print(f"--> Models loaded - glid")
    
    print(f"--> Loading model - swinir")
    swinir_model = swinir.load_model(is_real_sr=True)
    print(f"--> Model loaded - swinir")
    
    print("--> DALL-E Server is up and running!")


if __name__ == "__main__":
    print("flask main")
    app.run(host="0.0.0.0", port=port, debug=False)
