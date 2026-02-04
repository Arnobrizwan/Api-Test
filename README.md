# OCR Image Text Extraction API

A production-ready serverless OCR API built with FastAPI and deployed on Google Cloud Run. Extracts text from images using Google Cloud Vision API (primary) with Tesseract OCR as fallback.

**Version:** 1.2.0

## Features

- **Dual OCR Engines**: Google Cloud Vision API (primary) + Tesseract OCR (fallback)
- **Multiple Image Formats**: JPG, JPEG, PNG, GIF, WebP, BMP, TIFF
- **Batch Processing**: Process up to 10 images in a single request
- **Result Caching**: SHA256-based caching with Redis or in-memory storage
- **Entity Extraction**: Automatically extracts emails, phone numbers, URLs, dates
- **Image Metadata**: Returns dimensions, format, EXIF data, color analysis
- **Quality Assessment**: Evaluates image quality and provides recommendations
- **Rate Limiting**: Configurable rate limits per endpoint
- **API Key Authentication**: Secure endpoints with X-API-Key header
- **Security Scanning**: Magic byte validation, content scanning, input sanitization
- **Web Dashboard**: Interactive frontend for testing the API
- **Health Monitoring**: Dependency health checks for Vision API, Tesseract, Redis

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── constants.py        # Application constants and enums
│   │   ├── exceptions.py       # Custom exception classes
│   │   ├── logging.py          # Structured logging setup
│   │   └── security.py         # Security utilities (validation, sanitization)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── ocr.py              # OCR API endpoints
│   ├── services/
│   │   ├── ocr_service.py      # OCR orchestration service
│   │   ├── vision_api.py       # Google Cloud Vision integration
│   │   └── tesseract.py        # Tesseract OCR integration
│   ├── models/
│   │   └── responses.py        # Pydantic response models
│   └── utils/
│       ├── validators.py       # Image validation utilities
│       ├── image_utils.py      # Image preprocessing
│       ├── text_processing.py  # Text cleanup and entity extraction
│       ├── metadata.py         # Image metadata extraction
│       └── cache_manager.py    # Redis/in-memory caching
├── frontend/                   # Web dashboard (HTML/CSS/JS)
├── tests/
│   ├── sample_images/          # Test images
│   ├── test_ocr_endpoint.py
│   └── test_validators.py
├── Dockerfile
├── requirements.txt
├── commands.md                 # Testing commands reference
├── documentation.md            # API documentation
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| GET | `/health` | Health check with dependency status |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |
| GET | `/web` | Interactive web dashboard |
| POST | `/v1/extract-text` | Extract text from single image |
| POST | `/v1/extract-text/batch` | Extract text from multiple images (up to 10) |
| GET | `/v1/cache/stats` | Cache statistics |
| DELETE | `/v1/cache` | Clear cache |

## Quick Start

### Extract Text from Image

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@test_image.jpg" \
  https://your-service-url/v1/extract-text
```

### Batch Processing

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "images=@image1.jpg" \
  -F "images=@image2.png" \
  https://your-service-url/v1/extract-text/batch
```

### Success Response

```json
{
  "success": true,
  "text": "Extracted text content",
  "text_formatted": "Cleaned and formatted text",
  "confidence": 0.95,
  "processing_time_ms": 1234,
  "ocr_engine": "cloud_vision",
  "cached": false,
  "text_stats": {
    "word_count": 10,
    "character_count": 50,
    "character_count_no_spaces": 41,
    "line_count": 2
  },
  "entities": {
    "emails": ["test@example.com"],
    "phone_numbers": [],
    "urls": [],
    "dates": []
  },
  "image_metadata": {
    "width": 800,
    "height": 600,
    "format": "JPEG",
    "mode": "RGB"
  },
  "quality_assessment": {
    "score": 85,
    "quality": "good",
    "recommendations": []
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE"
}
```

## Error Codes

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | INVALID_FILE_TYPE | Unsupported file format |
| 400 | FILE_TOO_LARGE | File exceeds 10MB limit |
| 400 | INVALID_IMAGE | Corrupted or invalid image |
| 401 | UNAUTHORIZED | Missing or invalid API key |
| 422 | MISSING_FILE | No file uploaded |
| 429 | RATE_LIMIT_EXCEEDED | Rate limit exceeded |
| 500 | OCR_FAILED | OCR processing failed |

## Local Development

### Prerequisites

- Python 3.11+
- Tesseract OCR installed
- Google Cloud credentials (optional, for Vision API)
- Redis (optional, for distributed caching)

### Setup

1. **Clone and setup virtual environment:**
   ```bash
   cd "Api Test"
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install Tesseract:**
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-eng

   # Windows - Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Configure environment (create .env file):**
   ```env
   # API Security
   API_KEY=your-secret-api-key

   # Google Cloud (optional)
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   GCP_PROJECT_ID=your-project-id

   # Cache Configuration
   CACHE_TYPE=in-memory  # or "redis"
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=
   REDIS_SSL=false

   # Rate Limiting
   RATE_LIMIT=60/minute
   RATE_LIMIT_BATCH=10/minute

   # Logging
   LOG_LEVEL=INFO
   DEBUG=false
   ```

4. **Run locally:**
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

5. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

## Docker

### Build and Run

```bash
# Build
docker build -t ocr-api .

# Run with Tesseract only
docker run -p 8080:8080 -e API_KEY=your-key ocr-api

# Run with Vision API
docker run -p 8080:8080 \
  -e API_KEY=your-key \
  -e GOOGLE_APPLICATION_CREDENTIALS=/creds/key.json \
  -v ~/.config/gcloud/application_default_credentials.json:/creds/key.json:ro \
  ocr-api
```

## Cloud Run Deployment

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com vision.googleapis.com artifactregistry.googleapis.com

# Build and deploy
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ocr-api/ocr-service
gcloud run deploy ocr-service \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ocr-api/ocr-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --min-instances 1
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | - | API key for authentication (required in production) |
| `GOOGLE_APPLICATION_CREDENTIALS` | - | Path to GCP service account key |
| `GCP_PROJECT_ID` | - | Google Cloud project ID |
| `USE_TESSERACT_ONLY` | `false` | Skip Vision API, use only Tesseract |
| `MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10MB) |
| `MAX_BATCH_SIZE` | `10` | Max images per batch request |
| `CACHE_TYPE` | `in-memory` | Cache backend: `in-memory` or `redis` |
| `CACHE_TTL_SECONDS` | `3600` | Cache entry TTL |
| `REDIS_HOST` | `localhost` | Redis server host |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_PASSWORD` | - | Redis password |
| `REDIS_SSL` | `false` | Enable SSL for Redis connection |
| `RATE_LIMIT` | `60/minute` | Rate limit for single image endpoint |
| `RATE_LIMIT_BATCH` | `10/minute` | Rate limit for batch endpoint |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Enable debug mode |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

## Architecture

```
┌─────────────┐     ┌────────────────────────────────────────┐
│   Client    │────▶│           Cloud Run (FastAPI)          │
│  (curl/app) │     │                                        │
└─────────────┘     │  ┌──────────┐    ┌─────────────────┐   │
                    │  │   Rate   │    │   API Key       │   │
                    │  │  Limiter │    │  Validation     │   │
                    │  └────┬─────┘    └────────┬────────┘   │
                    │       │                   │            │
                    │       ▼                   ▼            │
                    │  ┌─────────────────────────────────┐   │
                    │  │        OCR Service              │   │
                    │  │  ┌─────────┐   ┌────────────┐   │   │
                    │  │  │ Vision  │   │ Tesseract  │   │   │
                    │  │  │   API   │──▶│ (fallback) │   │   │
                    │  │  └─────────┘   └────────────┘   │   │
                    │  └──────────────┬──────────────────┘   │
                    │                 │                      │
                    │                 ▼                      │
                    │  ┌─────────────────────────────────┐   │
                    │  │    Redis / In-Memory Cache      │   │
                    │  └─────────────────────────────────┘   │
                    └────────────────────────────────────────┘
```

## License

MIT
