
FROM python:3.10-slim

RUN pip install --upgrade pip setuptools wheel
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
ENV PIP_NO_CUDA=1

RUN pip install torch==2.2.2
COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

COPY backend/ /app/backend

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
