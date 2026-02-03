# OCR Image Text Extraction API

A serverless OCR API built with FastAPI and deployed on Google Cloud Run. Extracts text from JPG/JPEG images using Google Cloud Vision API as the primary OCR engine with Tesseract as a fallback.

## Features

- **Dual OCR Engines**: Google Cloud Vision API (primary) + Tesseract OCR (fallback)
- **Confidence Scores**: Returns confidence scores for extracted text
- **Image Validation**: Validates file type, size, and integrity
- **Processing Metrics**: Reports processing time in milliseconds
- **Serverless Deployment**: Designed for Google Cloud Run
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routes/
│   │   └── ocr.py           # OCR endpoint
│   ├── services/
│   │   ├── ocr_service.py   # OCR orchestration
│   │   ├── vision_api.py    # Google Cloud Vision
│   │   └── tesseract.py     # Tesseract OCR
│   ├── models/
│   │   └── responses.py     # Pydantic models
│   └── utils/
│       ├── validators.py    # Image validation
│       └── image_utils.py   # Image preprocessing
├── tests/
│   ├── test_ocr_endpoint.py
│   └── test_validators.py
├── Dockerfile
├── requirements.txt
└── README.md
```

## API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| POST | `/extract-text` | Extract text from image |

### Extract Text Endpoint

```
POST /extract-text
Content-Type: multipart/form-data
```

**Request:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image | File | Yes | JPG/JPEG image file (max 10MB) |

**Success Response (200):**

```json
{
  "success": true,
  "text": "Extracted text content",
  "confidence": 0.95,
  "processing_time_ms": 1234,
  "ocr_engine": "cloud_vision"
}
```

**No Text Found Response (200):**

```json
{
  "success": true,
  "text": "",
  "confidence": 0.0,
  "processing_time_ms": 856,
  "ocr_engine": "cloud_vision"
}
```

### Error Responses

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | INVALID_FILE_TYPE | File is not JPG/JPEG |
| 400 | FILE_TOO_LARGE | File exceeds 10MB |
| 400 | INVALID_IMAGE | Image file is corrupted |
| 422 | MISSING_FILE | No file uploaded |
| 500 | OCR_FAILED | Both OCR engines failed |

**Error Response Format:**

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE"
}
```

## Local Development

### Prerequisites

- Python 3.11+
- Tesseract OCR installed
- Google Cloud credentials (optional, for Vision API)

### Setup

1. **Clone the repository:**
   ```bash
   cd "Api Test"
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract (if not already installed):**
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-eng

   # Windows
   # Download installer from https://github.com/UB-Mannheim/tesseract/wiki
   ```

5. **Set up Google Cloud credentials (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
   ```

### Run Locally

```bash
uvicorn app.main:app --reload --port 8080
```

The API will be available at `http://localhost:8080`.

### Run Tests

```bash
pytest tests/ -v
```

## Docker

### Build Image

```bash
docker build -t ocr-api .
```

### Run Container

```bash
# With Tesseract only
docker run -p 8080:8080 ocr-api

# With Google Cloud Vision API
docker run -p 8080:8080 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/creds/key.json \
  -v ~/.config/gcloud/application_default_credentials.json:/creds/key.json:ro \
  ocr-api
```

## Deployment to Google Cloud Run

### Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
2. A Google Cloud project with billing enabled

### Setup GCP

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable vision.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository
gcloud artifacts repositories create ocr-api \
    --repository-format=docker \
    --location=us-central1
```

### Build and Deploy

```bash
# Authenticate Docker with GCP
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push image
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ocr-api/ocr-service

# Deploy to Cloud Run
gcloud run deploy ocr-service \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ocr-api/ocr-service \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 10
```

### Get Service URL

```bash
gcloud run services describe ocr-service --region us-central1 --format 'value(status.url)'
```

## Usage Examples

### curl

```bash
# Local
curl -X POST \
  -F "image=@test_image.jpg" \
  http://localhost:8080/extract-text

# Cloud Run
curl -X POST \
  -F "image=@test_image.jpg" \
  https://your-service-url/extract-text
```

### Python

```python
import requests

url = "http://localhost:8080/extract-text"
files = {"image": open("test_image.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

### JavaScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('image', fs.createReadStream('test_image.jpg'));

axios.post('http://localhost:8080/extract-text', form, {
  headers: form.getHeaders()
}).then(response => {
  console.log(response.data);
});
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | - | Path to GCP service account key |
| `GCP_PROJECT_ID` | - | Google Cloud project ID |
| `USE_TESSERACT_ONLY` | `false` | Skip Vision API, use only Tesseract |
| `MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10MB) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PORT` | `8080` | Server port |

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   Client    │────▶│   Cloud Run      │────▶│  Google Cloud       │
│  (curl/app) │     │   (FastAPI)      │     │  Vision API         │
└─────────────┘     │                  │     └─────────────────────┘
                    │  ┌────────────┐  │              │
                    │  │ Tesseract  │  │◀─────────────┘
                    │  │ (fallback) │  │     (if Vision fails)
                    │  └────────────┘  │
                    └──────────────────┘
```

## License

MIT
