# Dockerfile
FROM python:3.8-slim

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential \
 && rm -rf /var/lib/apt/lists/*

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


# Install TensorFlow 2.3.0 (CPU)
RUN pip install tensorflow-cpu==2.3.0 \
 && pip install protobuf==3.20.3

# Upgrade pip & install SNAF from the specific commit
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install "git+https://github.com/frankligy/SNAF.git@e23ce39512a1a7f58c74e59b4b7cedc89248b908"

WORKDIR /workspace


CMD ["python", "-c", "import snaf, tensorflow as tf; print('SNAF OK, TF', tf.__version__)"]