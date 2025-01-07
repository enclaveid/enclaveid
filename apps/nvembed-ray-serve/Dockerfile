# Dockerfile for k8s deployment
FROM rayproject/ray:2.40.0-py312-gpu

ENV HF_HUB_ENABLE_HF_TRANSFER=1

# Set working directory
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dist/nvembed_ray_serve-*.whl .
RUN pip install nvembed_ray_serve-*.whl --no-deps


EXPOSE 8265 8000 10001 6379


