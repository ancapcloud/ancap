FROM python:3.12-slim
ARG WEVISONE_COMMIT=9a6bcd85404505df0d05cfb5d97512ccacf35dee
RUN apt-get update && apt-get install -y --no-install-recommends git libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
RUN git clone https://github.com/Tencent/WeVisOne-VL.git /opt/wevisone && cd /opt/wevisone && git checkout "$WEVISONE_COMMIT" && pip install --no-cache-dir . && rm -rf .git
RUN pip install --no-cache-dir fastapi==0.121.3 uvicorn==0.38.0
WORKDIR /worker
COPY scripts/wevisone_payment_worker.py scripts/wevisone_payment_worker.py
COPY app/services/payment_vision_prompt.py app/services/payment_vision_prompt.py
ENV HF_HOME=/cache/huggingface PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
EXPOSE 8097
CMD ["python", "-m", "uvicorn", "scripts.wevisone_payment_worker:app", "--host", "0.0.0.0", "--port", "8097", "--workers", "1", "--no-access-log"]

