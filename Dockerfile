# Smart Sampler API - Official Dockerfile (Nov 2025 – Coolify-optimized)
FROM python:3.10-slim

# System deps for audio (librosa + madmom)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip (fastest + most reliable method 2025)
RUN pip install --no-cache-dir uv

WORKDIR /appimage.png

# Copy only what we need for install (layer caching)
COPY pyproject.toml .
COPY audio_backend_api.py .
COPY sitecustomize.py .

# Create virtual environment and install dependencies in stages
# First install build dependencies and numpy (madmom needs it at build time)
RUN uv venv && \
    uv pip install 'numpy<2' Cython setuptools && \
    uv pip install scipy soundfile && \
    uv pip install madmom && \
    uv pip install robyn librosa deepgram-sdk python-dotenv python-multipart && \
    cp sitecustomize.py .venv/lib/python3.10/site-packages/

# Expose Coolify/Traefik port
EXPOSE 8080

# Set environment variables for Robyn
ENV ROBYN_HOST=0.0.0.0
ENV ROBYN_PORT=8080

# Run with maximum performance
CMD ["uv", "run", "python", "audio_backend_api.py", "--processes", "4", "--workers", "2"]
