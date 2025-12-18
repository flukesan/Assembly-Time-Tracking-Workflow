FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    SETUPTOOLS_USE_DISTUTILS=stdlib

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python
    python3.11 \
    python3.11-dev \
    python3-pip \
    # Build tools (required for some packages)
    build-essential \
    gcc \
    g++ \
    cmake \
    # Database
    libpq-dev \
    # OpenCV dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    # Video processing
    ffmpeg \
    # OCR
    tesseract-ocr \
    tesseract-ocr-tha \
    # Networking
    curl \
    wget \
    # Development tools
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip using Python 3.11
RUN python3.11 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install remaining Python dependencies
# Note: lap package is intentionally skipped - ByteTrack will use scipy.optimize.linear_sum_assignment
#       as a fallback which provides the same optimal solution without compilation requirements
# PyTorch GPU version will be installed from requirements.txt (torch==2.1.2, torchvision==0.16.2)
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs /app/data/recordings

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python3.11 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start application
CMD ["python3.11", "src/main.py"]
