FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
