FROM nvidia/cuda:11.4.3-cudnn8-devel-ubuntu20.04

# expose
EXPOSE 8080

# set working directory
WORKDIR /app

# install pip
RUN apt-get update && apt-get install -y python3-pip

# install git
RUN apt-get install -y git

# update pip
RUN pip3 install --upgrade pip

## glid
ENV PATH="/root/miniconda3/bin:$PATH"
ARG PATH="/root/miniconda3/bin:$PATH"

RUN apt-get install -y wget && rm -rf /var/lib/apt/lists/*

RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh 

RUN conda --version

COPY ./environment.yaml /app/environment.yaml

RUN conda env create -f environment.yaml
SHELL ["conda", "run", "-n", "ldm", "/bin/bash", "-c"]

RUN wget https://dall-3.com/models/glid-3-xl/bert.pt \
    && wget https://dall-3.com/models/glid-3-xl/kl-f8.pt \
    && wget https://dall-3.com/models/glid-3-xl/finetune.pt

# add requirements
COPY ./requirements.txt /app/requirements.txt

# install requirements
RUN pip3 install -r requirements.txt

# install jax[cuda]
RUN pip3 install --upgrade "jax[cuda]" -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html

# add source code
COPY . /app

# run server
CMD python3 app.py --port 8080 --model_version mini
