# OCR API Documentation

A powerful OCR (Optical Character Recognition) API that extracts text from images using Google Cloud Vision API with Tesseract as fallback.

**Base URL:** `https://ocr-service-243539984009.us-central1.run.app`

---

## Quick Start

Extract text from an image in seconds using the sample image:

```bash
curl -X POST -F "image=@tests/sample_images/text_sample.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

That's it! You'll get back the extracted text in JSON format.

---

## Endpoints

### 1. Extract Text from Single Image

**POST** `/extract-text`

Upload an image and get the extracted text back.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | File | Yes | Image file to process |

**Supported Formats:** JPG, JPEG, PNG, GIF, BMP, TIFF, WebP, HEIC

**Max File Size:** 10MB

#### How to Upload

**Using curl:**
```bash
curl -X POST \
  -F "image=@tests/sample_images/text_sample.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**Using Python:**
```python
import requests

url = "https://ocr-service-243539984009.us-central1.run.app/extract-text"
files = {"image": open("tests/sample_images/text_sample.jpg", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

**Using JavaScript (Node.js):**
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('image', fs.createReadStream('tests/sample_images/text_sample.jpg'));

axios.post('https://ocr-service-243539984009.us-central1.run.app/extract-text', form, {
  headers: form.getHeaders()
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

**POST** `/extract-text/batch`

Process multiple images in a single request.

#### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `images` | Files | Yes | Multiple image files (up to 10) |

#### How to Upload

**Using curl:**
```bash
curl -X POST \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/test.png" \
  -F "images=@tests/sample_images/small.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/extract-text/batch
```

**Using Python:**
```python
import requests

url = "https://ocr-service-243539984009.us-central1.run.app/extract-text/batch"
files = [
    ("images", open("tests/sample_images/text_sample.jpg", "rb")),
    ("images", open("tests/sample_images/test.png", "rb")),
    ("images", open("tests/sample_images/small.jpg", "rb"))
]

response = requests.post(url, files=files)
print(response.json())
```

#### Success Response (200 OK)

```json
{
  "success": true,
  "total_files": 3,
  "successful": 3,
  "failed": 0,
  "total_processing_time_ms": 580,
  "results": [
    {
      "filename": "text_sample.jpg",
      "success": true,
      "text": "Hello, World!\nThis is a sample OCR test image.\nTesting 123... Special chars: @#$%",
      "text_formatted": "Hello, World! This is a sample OCR test image. Testing 123... Special chars: @#$%",
      "confidence": 0.9768,
      "ocr_engine": "cloud_vision",
      "cached": true,
      "processing_time_ms": 0
    },
    {
      "filename": "test.png",
      "success": true,
      "text": "PNG Test Image",
      "text_formatted": "PNG Test Image",
      "confidence": 0.9812,
      "ocr_engine": "cloud_vision",
      "cached": false,
      "processing_time_ms": 322
    },
    {
      "filename": "small.jpg",
      "success": true,
      "text": "Small text",
      "text_formatted": "Small text",
      "confidence": 0.9262,
      "ocr_engine": "cloud_vision",
      "cached": false,
      "processing_time_ms": 258
    }
  ]
}
```

---

### 3. Health Check

**GET** `/health`

Check if the API is running and which OCR engines are available.

```bash
curl https://ocr-service-243539984009.us-central1.run.app/health
```

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ocr_engines": {
    "cloud_vision": true,
    "tesseract": true
  }
}
```

---

### 4. API Info

**GET** `/`

Get general information about the API.

```bash
curl https://ocr-service-243539984009.us-central1.run.app/
```

#### Response

```json
{
  "name": "OCR Image Text Extraction API",
  "version": "1.0.0",
  "description": "Extract text from images using Google Cloud Vision API with Tesseract fallback",
  "endpoints": {
    "extract_text": "POST /extract-text",
    "batch_extract": "POST /extract-text/batch",
    "health": "GET /health"
  }
}
```

---

## Error Responses

The API returns clear error messages when something goes wrong.

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
| 400 | `INVALID_FILE_TYPE` | File is not a supported image format | Uploading a .pdf file |
| 400 | `INVALID_IMAGE` | Image file is corrupted or unreadable | Damaged image file |
| 400 | `INVALID_CONTENT` | File content doesn't match extension | .jpg file that's actually a .txt |
| 413 | `FILE_TOO_LARGE` | File exceeds 10MB limit | 15MB image upload |
| 422 | `MISSING_FILE` | No file was uploaded | Empty request |
| 429 | `RATE_LIMITED` | Too many requests | Exceeded 100 requests/minute |
| 500 | `OCR_FAILED` | OCR processing failed | Both engines failed |
| 500 | `INTERNAL_ERROR` | Unexpected server error | Server issue |

### Example Error Responses

**Invalid file type:**
```bash
curl -X POST -F "image=@document.pdf" https://ocr-service-243539984009.us-central1.run.app/extract-text
```
```json
{
  "success": false,
  "error": "Invalid file type. Allowed: jpg, jpeg, png, gif, bmp, tiff, webp, heic",
  "error_code": "INVALID_FILE_TYPE"
}
```

**File too large:**
```json
{
  "success": false,
  "error": "File size exceeds maximum limit of 10MB",
  "error_code": "FILE_TOO_LARGE"
}
```

**No text found (not an error - returns empty text):**
```bash
curl -X POST -F "image=@tests/sample_images/no_text.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```
```json
{
  "success": true,
  "text": "",
  "text_formatted": "",
  "confidence": 0.0,
  "processing_time_ms": 300,
  "ocr_engine": "cloud_vision",
  "cached": false
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
| `rotated.jpg` | Rotated text to test deskew feature |
| `invoice.jpg` | Invoice with structured text |
| `small.jpg` | Small image to test upscaling |
| `no_text.jpg` | Image without text |
| `test.png` | PNG format test |

### Test with Sample Images

**Basic text extraction:**
```bash
curl -X POST -F "image=@tests/sample_images/text_sample.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**High quality image:**
```bash
curl -X POST -F "image=@tests/sample_images/high_quality.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**Low quality image (tests preprocessing):**
```bash
curl -X POST -F "image=@tests/sample_images/low_quality.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**Rotated text (tests auto-deskew):**
```bash
curl -X POST -F "image=@tests/sample_images/rotated.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**Invoice with structured data:**
```bash
curl -X POST -F "image=@tests/sample_images/invoice.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**Small image (tests upscaling):**
```bash
curl -X POST -F "image=@tests/sample_images/small.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**PNG format:**
```bash
curl -X POST -F "image=@tests/sample_images/test.png" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

**Image with no text (edge case):**
```bash
curl -X POST -F "image=@tests/sample_images/no_text.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

### Test Batch Processing

Process multiple sample images at once:
```bash
curl -X POST \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/invoice.jpg" \
  -F "images=@tests/sample_images/high_quality.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/extract-text/batch
```

### Test Health Check

```bash
curl https://ocr-service-243539984009.us-central1.run.app/health
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/extract-text` | 100 requests per minute |
| `/extract-text/batch` | 20 requests per minute |

If you exceed the limit, you'll receive:
```json
{
  "success": false,
  "error": "Rate limit exceeded. Try again later.",
  "error_code": "RATE_LIMITED"
}
```

---

## Tips for Best Results

1. **Image Quality:** Higher resolution images produce better results
2. **Contrast:** Ensure good contrast between text and background
3. **Orientation:** The API auto-corrects skewed images, but straight images work best
4. **File Size:** Larger files take longer to process; optimize if speed matters
5. **Caching:** Identical images are cached - subsequent requests are faster

---

## Interactive Documentation

Visit the Swagger UI for interactive API testing:

**Swagger UI:** `https://ocr-service-243539984009.us-central1.run.app/docs`

**ReDoc:** `https://ocr-service-243539984009.us-central1.run.app/redoc`

---

## Support

Having issues? Check these common solutions:

| Problem | Solution |
|---------|----------|
| "Invalid file type" | Make sure you're uploading an image (JPG, PNG, etc.) |
| "File too large" | Compress or resize your image under 10MB |
| Low confidence score | Try a higher resolution image with better lighting |
| Empty text result | The image might not contain readable text |

---

## Changelog

**v1.0.0** - Initial Release
- Single image OCR extraction
- Batch processing (up to 10 images)
- Google Cloud Vision API + Tesseract fallback
- Advanced image preprocessing for better accuracy
- Caching for identical images
- Rate limiting
- Entity extraction (emails, phones, URLs, dates)
- Image metadata and quality assessment
