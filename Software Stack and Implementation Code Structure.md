Operating System: Ubuntu 22.04 LTS

Containerization:
  - Docker + Docker Compose
  
Services:
  postgresql:
    image: timescale/timescaledb:latest-pg15
    volumes: ./postgres_data:/var/lib/postgresql/data
    
  qdrant:
    image: qdrant/qdrant:latest
    ports: 6333:6333
    volumes: ./qdrant_storage:/qdrant/storage
    
  redis:
    image: redis:7-alpine
    
  ollama:
    image: ollama/ollama:latest
    volumes: ./ollama_models:/root/.ollama
    
  app:
    build: .
    depends_on: [postgresql, qdrant, redis, ollama]
```

---

## 🔧 Implementation Code Structure
```
assembly-time-tracking/
├── src/
│   ├── camera/
│   │   ├── camera_manager.py          # Multi-camera handling
│   │   ├── rtsp_stream.py
│   │   └── usb_camera.py
│   │
│   ├── ai/
│   │   ├── yolo_detector.py           # Person detection
│   │   ├── tracker.py                 # DeepSORT/ByteTrack
│   │   ├── motion_detector.py
│   │   └── sequence_model.py          # Process sequence analysis
│   │
│   ├── core/
│   │   ├── zone_manager.py            # Zone drawing & management
│   │   ├── time_tracker.py            # Time tracking logic
│   │   ├── index_manager.py           # Index calculation
│   │   └── schedule_manager.py        # Work schedule
│   │
│   ├── data/
│   │   ├── postgres_manager.py        # PostgreSQL operations
│   │   ├── qdrant_manager.py          # Qdrant operations
│   │   ├── redis_manager.py           # Cache
│   │   └── etl_pipeline.py            # PostgreSQL → Qdrant ETL
│   │
│   ├── rag/
│   │   ├── embedding_service.py       # Text embedding
│   │   ├── query_router.py            # Route queries
│   │   ├── retriever.py               # Vector search
│   │   ├── llm_service.py             # LLM interaction
│   │   └── rag_engine.py              # Main RAG orchestrator
│   │
│   ├── api/
│   │   ├── fastapi_app.py             # REST API
│   │   ├── websocket_server.py        # Real-time updates
│   │   └── endpoints/
│   │       ├── tracking.py
│   │       ├── analytics.py
│   │       └── query.py               # RAG query endpoint
│   │
│   └── ui/
│       ├── main_window.py             # PyQt6 main window
│       ├── camera_view.py             # Grid display
│       ├── zone_editor.py             # Zone drawing
│       ├── dashboard.py               # Analytics dashboard
│       └── chat_interface.py          # RAG query interface
│
├── config/
│   ├── camera_config.yaml
│   ├── zone_config.yaml
│   ├── schedule_config.yaml
│   └── qdrant_collections.yaml
│
├── docker-compose.yml
├── requirements.txt
└── README.md
