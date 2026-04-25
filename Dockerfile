# Use the specific Python 3.11.8 image
FROM python:3.11.8-slim

# Install Redis server
RUN apt-get update && apt-get install -y redis-server && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /PORTAL_BACKEND

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project (app folder, .env, etc.)
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start Redis, then Celery (background), then FastAPI (foreground)
CMD redis-server --port 6380 --daemonize yes && \
    python -m app.backgroundTasks.celery_worker & \
    uvicorn app.main:app --host 0.0.0.0 --port 8000

    