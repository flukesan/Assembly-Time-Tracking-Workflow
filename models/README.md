# YOLOv8 Models Directory

This directory stores YOLOv8 model weights.

## Download Models

Run the download script:
```bash
./scripts/download_models_local.sh
```

This will download:
- yolov8n.pt (6 MB) - Nano model
- yolov8s.pt (22 MB) - Small model
- yolov8m.pt (52 MB) - Medium model

## Usage

Models are automatically loaded by the YOLODetector class in `src/ai/yolo_detector.py`.

Configure the model in `config/config.yaml`:
```yaml
detection:
  model_name: "yolov8n.pt"
```

