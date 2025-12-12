#!/bin/bash

# Download YOLOv8 Models Script (Local - Outside Docker)
# Run this on your host machine to download models

set -e

echo "======================================"
echo "YOLOv8 Model Download Script (Local)"
echo "======================================"
echo ""

# Create models directory in project root
MODELS_DIR="./models"
mkdir -p "$MODELS_DIR"

echo "📁 Models directory: $MODELS_DIR"
echo ""

# Download YOLOv8 models
echo "📥 Downloading YOLOv8 models..."
echo ""

# YOLOv8n (Nano - Fastest, smallest)
if [ ! -f "$MODELS_DIR/yolov8n.pt" ]; then
    echo "  ⏬ Downloading yolov8n.pt (6 MB)..."
    wget -q --show-progress -O "$MODELS_DIR/yolov8n.pt" \
        https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt || \
    curl -L -o "$MODELS_DIR/yolov8n.pt" \
        https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt
    echo "  ✅ yolov8n.pt downloaded"
else
    echo "  ✅ yolov8n.pt already exists"
fi

# YOLOv8s (Small - Balanced)
if [ ! -f "$MODELS_DIR/yolov8s.pt" ]; then
    echo "  ⏬ Downloading yolov8s.pt (22 MB)..."
    wget -q --show-progress -O "$MODELS_DIR/yolov8s.pt" \
        https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt || \
    curl -L -o "$MODELS_DIR/yolov8s.pt" \
        https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt
    echo "  ✅ yolov8s.pt downloaded"
else
    echo "  ✅ yolov8s.pt already exists"
fi

echo ""
echo "======================================"
echo "✅ Model download complete!"
echo "======================================"
echo ""
echo "Available models:"
ls -lh "$MODELS_DIR"/*.pt 2>/dev/null || echo "No models found"
echo ""
echo "Model comparison:"
echo "  yolov8n.pt - Nano (6 MB)   - Fastest, lowest accuracy (~30 FPS on CPU)"
echo "  yolov8s.pt - Small (22 MB) - Balanced speed/accuracy (~15 FPS on CPU)"
echo ""
echo "💡 Models will be mounted to Docker container at /app/models/"
echo ""
