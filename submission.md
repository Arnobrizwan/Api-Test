# OCR Image Text Extraction API - Submission

## 1. Public URLs
- **API Base:** `https://ocr-service-243539984009.us-central1.run.app`
- **Interactive Dashboard:** `https://ocr-service-243539984009.us-central1.run.app/web/`
- **API Docs (Swagger):** `https://ocr-service-243539984009.us-central1.run.app/docs`

---

## 2. Authentication
This API is secured with API Key authentication.
- **Header Name:** `X-API-Key`
- **Current Key:** `OCR_Secret_2026_!`

*Note: For the interactive dashboard, enter the key in the field at the top of the page.*

---

## 3. API Documentation

### HTTP Endpoints (v1)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/v1/extract-text` | Process a single image. |
| `POST` | `/v1/extract-text/batch` | Process up to 10 images (Returns 207 for mixed results). |
| `GET` | `/v1/cache/stats` | View performance metrics and Redis status. |
| `GET` | `/health` | Public health check. |

### Request Format (`/v1/extract-text`)
- **Headers:** `X-API-Key: OCR_Secret_2026_!`
- **Body:** `multipart/form-data` with field `image`.

### Example Testing (curl)
```bash
curl -X POST \
  -H "X-API-Key: OCR_Secret_2026_!" \
  -F "image=@test.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text
```

---

## 4. Implementation Details

### Core Features (Completed)
- ✅ **Dual OCR Engines:** Cloud Vision (Primary) + Tesseract (Fallback).
- ✅ **Secure Validation:** Magic byte signature checking & content scanning.
- ✅ **Authentication:** X-API-Key header enforcement.
- ✅ **Performance:** Auto-resizing large images to 2000px and persistent Redis caching.
- ✅ **Frontend:** Modern interactive dashboard with batch support.

### Deployment & Infrastructure
- **Platform:** Google Cloud Run.
- **Resources:** 2 vCPU, 2GB RAM, Startup Boost enabled.
- **Latency:** `min-instances: 1` ensures no cold starts.
- **Cache:** Upstash Redis (Serverless) over TLS/SSL.

---

## 5. Security Hardening
- **CORS:** Disabled credentials for wildcard origins.
- **SSL:** Enforced `ssl_cert_reqs="required"` for Redis.
- **Data Privacy:** Internal engine errors and stack traces are sanitized in production responses.
- **Auth:** Mandatory API Key for all processing endpoints.