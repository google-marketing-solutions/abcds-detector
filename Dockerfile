FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create temp directories
RUN mkdir -p /tmp/cr_uploads /tmp/cr_reduced

ENV PORT=8080
ENV IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
