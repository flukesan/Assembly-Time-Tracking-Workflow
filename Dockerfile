FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Python
    python3.11 \
    python3-pip \
    python3-dev \
    build-essential \
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

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install numpy first (required by lap package)
RUN pip3 install --no-cache-dir numpy==1.26.3

# Install lap with --no-build-isolation (allows access to numpy)
RUN pip3 install --no-cache-dir --no-build-isolation lap==0.4.0

# Install remaining Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs /app/data/recordings

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python3 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start application
CMD ["python3", "src/main.py"]
