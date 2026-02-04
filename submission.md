# OCR Image Text Extraction API - Submission

## 1. Public URL
- **Service URL:** `https://ocr-service-243539984009.us-central1.run.app`
- **Interactive API Docs (Swagger):** `https://ocr-service-243539984009.us-central1.run.app/docs`
- **Health Check:** `https://ocr-service-243539984009.us-central1.run.app/health`

---

## 2. API Documentation

### Interactive Frontend
A modern, web-based dashboard is available for testing the API without any code:
- **URL:** [https://ocr-service-243539984009.us-central1.run.app/frontend/index.html](https://ocr-service-243539984009.us-central1.run.app/frontend/index.html) (If hosted)
- **Local Testing:** Open `frontend/index.html` in any web browser.

**Features of the Frontend:**
- **Single Image Upload:** Drag-and-drop support with real-time preview.
- **Batch Processing:** Process up to 10 images at once with a summary dashboard.
- **Visual Analytics:** Displays confidence scores, word counts, and metadata.
- **Entity Visualization:** Highlights extracted emails, phone numbers, and URLs.
- **Quality Assessment:** Visual progress bars for image quality and OCR optimization tips.

### HTTP Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/v1/extract-text` | Extract text, entities, and metadata from a single image. |
| `POST` | `/v1/extract-text/batch` | Process up to 10 images in one request (Returns 207 Multi-Status). |
| `GET` | `/v1/cache/stats` | View cache performance and Redis connection status. |
| `DELETE` | `/v1/cache` | Clear all cached results. |
| `GET` | `/health` | Service health status. |

### Request Format (`/v1/extract-text`)
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Body:**
    - `image`: File (Required. JPG, PNG, GIF, WebP, BMP, TIFF - Max 10MB)
    - `include_metadata`: Boolean (Default: true)
    - `include_entities`: Boolean (Default: true)

### Response Format (Success 200 OK)
```json
{
  "success": true,
  "text": "Extracted text content",
  "confidence": 0.95,
  "processing_time_ms": 1234,
  "ocr_engine": "cloud_vision",
  "cached": false,
  "text_stats": { "word_count": 10, "character_count": 50 },
  "image_metadata": { "width": 1920, "height": 1080, "format": "JPEG" }
}
```

### Possible Error Codes
- `INVALID_FILE_TYPE` (400): Unsupported format.
- `FILE_TOO_LARGE` (400): File exceeds 10MB.
- `INVALID_IMAGE` (400): Corrupted file or failed binary magic-byte check.
- `MISSING_FILE` (422): No image provided.
- `RATE_LIMIT_EXCEEDED` (429): Request limit reached.
- `OCR_FAILED` (500): Processing error.

### Example Testing
```bash
# Test Single Image
curl -X POST -F "image=@test_image.jpg" https://ocr-service-243539984009.us-central1.run.app/v1/extract-text

# Test Batch
curl -X POST -F "images=@img1.jpg" -F "images=@img2.png" https://ocr-service-243539984009.us-central1.run.app/v1/extract-text/batch
```

---

## 3. Implementation Explanation

### OCR Engines & Orchestration
The API uses a dual-engine architecture for maximum reliability:
1. **Primary:** **Google Cloud Vision API** for high-accuracy cloud-based extraction.
2. **Fallback:** **Tesseract OCR**, containerized locally to ensure the service remains functional even if cloud quotas are exceeded or network issues occur.

### Security & Validation
- **Magic Byte Validation:** The service checks the actual binary signature of files to prevent malicious scripts from being uploaded as images.
- **Content Scanning:** Scans for suspicious code patterns within the image binary (polyglot attack protection).
- **Sanitization:** All filenames and input data are sanitized to prevent path traversal and injection attacks.

### Performance Optimizations
- **Auto-Resizing:** High-resolution images are automatically downscaled to 2000px width before processing. This reduces processing time by ~40% without sacrificing accuracy.
- **Persistent Caching:** Integrated with **Upstash Redis** (Serverless) to store results based on SHA256 image hashes. Repeated uploads are returned in under 50ms.
- **Infrastructure:** Deployed on **Cloud Run** with `min-instances: 1` and `no-cpu-throttling` to ensure zero cold starts and consistent performance.

---

## 4. Repository Structure
- `app/`: Core FastAPI application logic.
- `tests/`: Automated test suite and sample images.
- `Dockerfile`: Multi-stage optimized build.
- `cloudbuild.yaml`: Automated GCP deployment pipeline.
- `requirements.txt`: Python dependencies.
