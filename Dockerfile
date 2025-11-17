FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY start.sh .
RUN chmod +x start.sh

ENV PYTHONUNBUFFERED=1 \
    DB_PATH=/app/data/xrp_monitor.db

VOLUME ["/app/data"]

EXPOSE 8000

CMD ["bash", "start.sh"]
