# OCR API Documentation

A powerful OCR (Optical Character Recognition) API that extracts text from images using Google Cloud Vision API with Tesseract as fallback.

**Version:** 1.2.0

**Base URL:** `https://ocr-service-243539984009.us-central1.run.app`

---

## Authentication

All `/v1/*` endpoints require API key authentication.

**Header:** `X-API-Key: YOUR_API_KEY`

Example:
```bash
curl -H "X-API-Key: YOUR_API_KEY" https://your-api-url/v1/extract-text
```

---

## Quick Start

Extract text from an image:

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@tests/sample_images/text_sample.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text
```

---

## Endpoints

### 1. Extract Text from Single Image

**POST** `/v1/extract-text`

Upload an image and get the extracted text back.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | Yes | Image file to process |
| `include_metadata` | Query | No | Include image metadata (default: true) |
| `include_entities` | Query | No | Extract entities like emails/phones (default: true) |
| `use_cache` | Query | No | Use caching for identical images (default: true) |

**Supported Formats:** JPG, JPEG, PNG, GIF, BMP, TIFF, WebP

**Max File Size:** 10MB

#### How to Upload

**Using curl:**
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@tests/sample_images/text_sample.jpg" \
  "https://ocr-service-243539984009.us-central1.run.app/v1/extract-text?include_metadata=true&include_entities=true"
```

**Using Python:**
```python
import requests

url = "https://ocr-service-243539984009.us-central1.run.app/v1/extract-text"
headers = {"X-API-Key": "YOUR_API_KEY"}
files = {"image": open("tests/sample_images/text_sample.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

**Using JavaScript (Node.js):**
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('image', fs.createReadStream('tests/sample_images/text_sample.jpg'));

axios.post('https://ocr-service-243539984009.us-central1.run.app/v1/extract-text', form, {
  headers: {
    ...form.getHeaders(),
    'X-API-Key': 'YOUR_API_KEY'
  }
}).then(res => console.log(res.data));
```

#### Success Response (200 OK)

```json
{
  "success": true,
  "text": "Hello, World!\nThis is a sample OCR test image.\nTesting 123... Special chars: @#$%",
  "text_formatted": "Hello, World! This is a sample OCR test image. Testing 123... Special chars: @#$%",
  "confidence": 0.9768,
  "processing_time_ms": 2516,
  "ocr_engine": "cloud_vision",
  "cached": false,
  "text_stats": {
    "word_count": 14,
    "character_count": 81,
    "character_count_no_spaces": 68,
    "line_count": 3
  },
  "entities": {
    "emails": [],
    "phone_numbers": [],
    "urls": [],
    "dates": []
  },
  "image_metadata": {
    "width": 600,
    "height": 200,
    "format": "JPEG",
    "mode": "RGB",
    "aspect_ratio": 3.0,
    "megapixels": 0.12,
    "has_transparency": false
  },
  "quality_assessment": {
    "score": 75,
    "quality": "good",
    "recommendations": ["Image resolution is low. OCR accuracy may be reduced."]
  }
}
```

#### Response Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request was successful |
| `text` | string | Raw extracted text |
| `text_formatted` | string | Cleaned and formatted text with proper paragraphs |
| `confidence` | float | OCR confidence score (0.0 to 1.0) |
| `processing_time_ms` | integer | How long processing took in milliseconds |
| `ocr_engine` | string | Which engine was used: `cloud_vision` or `tesseract` |
| `cached` | boolean | Whether result was served from cache |
| `text_stats` | object | Statistics about the extracted text |
| `entities` | object | Extracted entities (emails, phones, URLs, dates) |
| `image_metadata` | object | Information about the uploaded image |
| `quality_assessment` | object | Image quality score and recommendations |

---

### 2. Batch Processing (Multiple Images)

**POST** `/v1/extract-text/batch`

Process multiple images in a single request. Returns HTTP 207 if some images succeed and others fail.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `images` | Files | Yes | Multiple image files (up to 10) |
| `include_metadata` | Query | No | Include image metadata (default: false for performance) |
| `include_entities` | Query | No | Extract entities (default: false for performance) |
| `use_cache` | Query | No | Use caching (default: true) |

#### How to Upload

**Using curl:**
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/test.png" \
  -F "images=@tests/sample_images/small.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text/batch
```

**Using Python:**
```python
import requests

url = "https://ocr-service-243539984009.us-central1.run.app/v1/extract-text/batch"
headers = {"X-API-Key": "YOUR_API_KEY"}
files = [
    ("images", open("tests/sample_images/text_sample.jpg", "rb")),
    ("images", open("tests/sample_images/test.png", "rb")),
    ("images", open("tests/sample_images/small.jpg", "rb"))
]

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

#### Success Response (200 OK / 207 Multi-Status)

```json
{
  "success": true,
  "total_files": 3,
  "successful": 3,
  "failed": 0,
  "total_processing_time_ms": 1011,
  "results": [
    {
      "filename": "text_sample.jpg",
      "success": true,
      "text": "Hello, World!...",
      "text_formatted": "Hello, World!...",
      "confidence": 0.9768,
      "ocr_engine": "cloud_vision",
      "cached": true,
      "processing_time_ms": 0
    },
    {
      "filename": "test.png",
      "success": true,
      "text": "PNG Test Image",
      "confidence": 0.9812,
      "ocr_engine": "cloud_vision",
      "cached": false,
      "processing_time_ms": 322
    }
  ]
}
```

---

### 3. Cache Statistics

**GET** `/v1/cache/stats`

Get current cache statistics including hit rate and configuration.

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://ocr-service-243539984009.us-central1.run.app/v1/cache/stats
```

#### Response (Redis)

```json
{
  "type": "redis",
  "status": "connected",
  "ttl": 3600,
  "redis_version": "7.0.0",
  "used_memory_human": "1.5M",
  "total_keys": 42
}
```

#### Response (In-Memory)

```json
{
  "type": "in-memory",
  "max_size": 100,
  "ttl": 3600,
  "current_size": 15
}
```

---

### 4. Clear Cache

**DELETE** `/v1/cache`

Clear all cached OCR results.

```bash
curl -X DELETE -H "X-API-Key: YOUR_API_KEY" \
  https://ocr-service-243539984009.us-central1.run.app/v1/cache
```

#### Response

```json
{
  "success": true,
  "message": "Cache cleared successfully"
}
```

---

### 5. Health Check

**GET** `/health`

Check service health and dependency status. No authentication required.

```bash
curl https://ocr-service-243539984009.us-central1.run.app/health
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.2.0",
  "dependencies": {
    "vision_api": {
      "available": true,
      "version": null,
      "error": null
    },
    "tesseract": {
      "available": true,
      "version": "5.5.2",
      "error": null
    },
    "cache": {
      "available": true,
      "version": "7.0.0",
      "error": null
    }
  }
}
```

**Status Values:**
- `healthy` - All dependencies available
- `degraded` - Non-critical dependency unavailable (e.g., cache)
- `unhealthy` - Critical dependency unavailable (no OCR engine)

---

### 6. API Info

**GET** `/`

Get general information about the API.

```bash
curl https://ocr-service-243539984009.us-central1.run.app/
```

#### Response

```json
{
  "name": "OCR Image Text Extraction API",
  "version": "1.2.0",
  "description": "Extract text from images using OCR",
  "features": [
    "Multiple image formats (JPG, PNG, GIF, WebP, BMP, TIFF)",
    "Dual OCR engines (Cloud Vision + Tesseract fallback)",
    "Confidence scores",
    "Text preprocessing and formatting",
    "Entity extraction (emails, phones, URLs, dates)",
    "Image metadata and EXIF data",
    "Quality assessment",
    "Result caching",
    "Batch processing (up to 10 images)",
    "Rate limiting",
    "Security scanning"
  ],
  "endpoints": {
    "extract_text": "POST /v1/extract-text",
    "batch_extract": "POST /v1/extract-text/batch",
    "cache_stats": "GET /v1/cache/stats",
    "clear_cache": "DELETE /v1/cache",
    "health": "GET /health",
    "docs": "GET /docs"
  },
  "limits": {
    "max_file_size_mb": 10,
    "max_batch_size": 10,
    "rate_limit": "60/minute",
    "rate_limit_batch": "10/minute"
  }
}
```

---

## Error Responses

The API returns consistent error messages in JSON format.

### Error Response Format

```json
{
  "success": false,
  "error": "Description of what went wrong",
  "error_code": "ERROR_CODE"
}
```

### Error Codes Reference

| HTTP Status | Error Code | Description | Example |
|-------------|------------|-------------|---------|
| 400 | `INVALID_FILE_TYPE` | Unsupported image format | Uploading a .pdf file |
| 400 | `INVALID_IMAGE` | Corrupted or unreadable image | Damaged image file |
| 401 | `UNAUTHORIZED` | Missing or invalid API key | No X-API-Key header |
| 413 | `FILE_TOO_LARGE` | File exceeds 10MB limit | 15MB image upload |
| 422 | `MISSING_FILE` | No file was uploaded | Empty request |
| 422 | `TOO_MANY_FILES` | More than 10 files in batch | 11 images in batch |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests | Exceeded rate limit |
| 500 | `OCR_FAILED` | OCR processing failed | Both engines failed |
| 500 | `INTERNAL_ERROR` | Unexpected server error | Server issue |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/v1/extract-text` | 60 requests per minute |
| `/v1/extract-text/batch` | 10 requests per minute |

Rate limit exceeded response:
```json
{
  "success": false,
  "error": "Rate limit exceeded. Try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

---

## Testing Examples

Sample images are included in the `tests/sample_images/` directory:

| Image | Description |
|-------|-------------|
| `text_sample.jpg` | Standard text image for basic testing |
| `high_quality.jpg` | High resolution image |
| `low_quality.jpg` | Low quality image to test preprocessing |
| `rotated.jpg` | Rotated text |
| `invoice.jpg` | Invoice with structured text |
| `small.jpg` | Small image to test handling |
| `no_text.jpg` | Image without text |
| `test.png` | PNG format test |

### Test Commands

```bash
# Set your API key
export API_KEY="YOUR_API_KEY"

# Single image
curl -X POST -H "X-API-Key: $API_KEY" \
  -F "image=@tests/sample_images/text_sample.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text

# Batch processing
curl -X POST -H "X-API-Key: $API_KEY" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/invoice.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text/batch

# Health check
curl https://ocr-service-243539984009.us-central1.run.app/health

# Cache stats
curl -H "X-API-Key: $API_KEY" \
  https://ocr-service-243539984009.us-central1.run.app/v1/cache/stats
```

---

## Tips for Best Results

1. **Image Quality:** Higher resolution images produce better results
2. **Contrast:** Ensure good contrast between text and background
3. **Orientation:** The API handles various orientations, but straight images work best
4. **File Size:** Larger files take longer to process; optimize if speed matters
5. **Caching:** Identical images are cached - subsequent requests are instant

---

## Interactive Documentation

- **Swagger UI:** `https://ocr-service-243539984009.us-central1.run.app/docs`
- **ReDoc:** `https://ocr-service-243539984009.us-central1.run.app/redoc`
- **Web Dashboard:** `https://ocr-service-243539984009.us-central1.run.app/web`

---

## Changelog

**v1.2.0** - Production Release
- Added `/v1/` API versioning prefix
- Enhanced health check with dependency status
- Added request ID tracking in logs
- Static file cache headers
- Thread-safe service initialization
- Timing attack prevention for API key validation
- Redis SSL support
- Safe cache clearing (namespace-only)

**v1.1.0** - Feature Update
- Parallel batch processing
- Entity extraction (emails, phones, URLs, dates)
- Image quality assessment
- Redis caching support
- Rate limiting
- API key authentication

**v1.0.0** - Initial Release
- Single image OCR extraction
- Batch processing (up to 10 images)
- Google Cloud Vision API + Tesseract fallback
- Image preprocessing
- In-memory caching
