FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio and downloads
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/scripts ./scripts
COPY scripts/download_models.sh ./download_models.sh

# Download models (they will be placed in /app/models)
RUN chmod +x ./download_models.sh && ./download_models.sh

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]