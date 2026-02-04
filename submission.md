# OCR Image Text Extraction API - Submission

## 1. Public URLs

| Resource | URL |
|----------|-----|
| **API Base** | `https://ocr-service-243539984009.us-central1.run.app` |
| **Interactive Dashboard** | `https://ocr-service-243539984009.us-central1.run.app/web` |
| **API Documentation (Swagger)** | `https://ocr-service-243539984009.us-central1.run.app/docs` |
| **ReDoc** | `https://ocr-service-243539984009.us-central1.run.app/redoc` |
| **Health Check** | `https://ocr-service-243539984009.us-central1.run.app/health` |

---

## 2. Authentication

This API is secured with API Key authentication.

- **Header Name:** `X-API-Key`
- **API Key:** *(Provided separately via secure channel)*

> **Security Note:** API keys should never be committed to version control or shared in documentation files.

---

## 3. API Documentation

### Endpoints (v1)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | No | API information |
| `GET` | `/health` | No | Health check with dependency status |
| `POST` | `/v1/extract-text` | Yes | Extract text from single image |
| `POST` | `/v1/extract-text/batch` | Yes | Process up to 10 images (returns 207 for mixed results) |
| `GET` | `/v1/cache/stats` | Yes | View cache statistics |
| `DELETE` | `/v1/cache` | Yes | Clear cache |

### Request Format

**Single Image (`POST /v1/extract-text`):**
- **Headers:** `X-API-Key: YOUR_API_KEY`
- **Body:** `multipart/form-data` with field `image`

**Batch (`POST /v1/extract-text/batch`):**
- **Headers:** `X-API-Key: YOUR_API_KEY`
- **Body:** `multipart/form-data` with field `images` (multiple files)

### Example Testing

```bash
# Single image OCR
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@test.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text

# Batch processing
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "images=@image1.jpg" \
  -F "images=@image2.png" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text/batch

# Health check (no auth required)
curl https://ocr-service-243539984009.us-central1.run.app/health
```

### Response Format

**Success (200):**
```json
{
  "success": true,
  "text": "Extracted text content",
  "confidence": 0.95,
  "processing_time_ms": 1234,
  "ocr_engine": "cloud_vision"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_CODE"
}
```

---

## 4. Implementation Details

### OCR Service Used
- **Primary:** Google Cloud Vision API (DOCUMENT_TEXT_DETECTION + TEXT_DETECTION fallback)
- **Secondary:** Tesseract OCR (automatic fallback when Vision API unavailable)

### File Upload & Validation
1. **Format validation:** Magic byte signature checking for JPG, PNG, GIF, WebP, BMP, TIFF
2. **Size validation:** Maximum 10MB per file
3. **Security scanning:** Content scanning for suspicious patterns
4. **Filename sanitization:** Path traversal prevention

### Deployment Strategy
- **Platform:** Google Cloud Run (managed, serverless)
- **Container:** Docker with non-root user for security
- **Resources:** 2 vCPU, 2GB RAM, startup boost enabled
- **Scaling:** Min 1 instance (no cold starts), max 10 instances
- **Cache:** Upstash Redis (serverless) with TLS/SSL encryption

---

## 5. Features Implemented

### Core Requirements
- [x] Accept JPG image uploads via POST request
- [x] Extract text using OCR
- [x] Return extracted text in JSON format
- [x] Handle cases where no text is found
- [x] Deploy to Google Cloud Run
- [x] Provide public URL
- [x] Proper error handling

### Bonus Features
- [x] Multiple image formats (JPG, PNG, GIF, WebP, BMP, TIFF)
- [x] Confidence scores for extracted text
- [x] Text preprocessing and cleanup
- [x] Rate limiting (60/min single, 10/min batch)
- [x] SHA256-based caching for identical images
- [x] Batch processing endpoint (up to 10 images)
- [x] Image metadata extraction (dimensions, EXIF, color info)
- [x] Entity extraction (emails, phone numbers, URLs, dates)
- [x] Image quality assessment with recommendations
- [x] Interactive web dashboard
- [x] API key authentication
- [x] Health monitoring with dependency status

---

## 6. Security Hardening

| Security Measure | Implementation |
|-----------------|----------------|
| **Authentication** | X-API-Key header with timing-attack-safe comparison |
| **CORS** | Credentials disabled for wildcard origins |
| **SSL/TLS** | Enforced for Redis connection (`ssl_cert_reqs="required"`) |
| **Input Validation** | Magic bytes, file size, content scanning |
| **Error Sanitization** | Internal errors/stack traces hidden in production |
| **Container Security** | Non-root user, minimal base image |
| **Rate Limiting** | Per-IP rate limiting on all endpoints |

---

## 7. GitHub Repository

- **Repository:** *(Link to be provided)*
- **Contents:**
  - Complete source code
  - Dockerfile
  - README with setup instructions
  - Sample test images in `tests/sample_images/`
  - API documentation
  - Testing commands reference

---

## 8. Architecture Overview

```
Client Request
      │
      ▼
┌─────────────────────────────────────────────────────┐
│                Google Cloud Run                      │
│  ┌─────────────────────────────────────────────┐    │
│  │              FastAPI Application             │    │
│  │                                              │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│  │  │   Rate   │  │  API Key │  │  Input   │  │    │
│  │  │  Limiter │─▶│  Auth    │─▶│ Validate │  │    │
│  │  └──────────┘  └──────────┘  └──────────┘  │    │
│  │                      │                      │    │
│  │                      ▼                      │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │           OCR Service                 │  │    │
│  │  │  ┌────────────┐  ┌────────────────┐  │  │    │
│  │  │  │Cloud Vision│  │   Tesseract    │  │  │    │
│  │  │  │   (1st)    │─▶│   (fallback)   │  │  │    │
│  │  │  └────────────┘  └────────────────┘  │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                      │                      │    │
│  │                      ▼                      │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │         Redis Cache (Upstash)        │  │    │
│  │  │         TLS/SSL Encrypted            │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 9. Version

**Current Version:** 1.2.0

**Key Updates in v1.2.0:**
- API versioning (`/v1/` prefix)
- Enhanced health checks with dependency monitoring
- Request ID tracking for debugging
- Static file caching headers
- Thread-safe initialization
- Timing attack prevention
- Redis SSL support
