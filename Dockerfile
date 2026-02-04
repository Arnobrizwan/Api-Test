FROM python:3.11-slim

# Suppress debconf warnings and set optimization env vars
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Install system dependencies including Tesseract
# Combined into one layer and cleaned up to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and frontend (done last as these change most frequently)
COPY app/ ./app/
COPY frontend/ ./frontend/

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Run the application using Gunicorn for better process management
# - k uvicorn.workers.UvicornWorker: Use uvicorn workers for ASGI support
# - --threads: Number of threads per worker
# - --workers: 1 (Cloud Run usually handles scaling by instances, but gunicorn manages the process lifecycle better)
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --threads 8 app.main:app
