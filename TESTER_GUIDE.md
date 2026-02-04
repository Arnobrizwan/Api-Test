# OCR API - Tester Guide

## API URL
```
https://ocr-service-243539984009.us-central1.run.app
```

## API Key
```
OCR_Secret_2026
```

---

## Quick Test Commands

### 1. Health Check (No Auth Required)
```bash
curl https://ocr-service-243539984009.us-central1.run.app/health
```

### 2. Extract Text from Image
```bash
curl -X POST \
  -H "X-API-Key: OCR_Secret_2026" \
  -F "image=@your_image.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text
```

### 3. Batch Processing (Multiple Images)
```bash
curl -X POST \
  -H "X-API-Key: OCR_Secret_2026" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text/batch
```

---

## Web Dashboard

For easy testing without command line, use the interactive dashboard:

**URL:** https://ocr-service-243539984009.us-central1.run.app/web

1. Enter your API key in the field at the top
2. Upload an image
3. Click "Extract Text"

---

## API Documentation

**Swagger UI:** https://ocr-service-243539984009.us-central1.run.app/docs

**ReDoc:** https://ocr-service-243539984009.us-central1.run.app/redoc

---

## Supported Formats

- JPG / JPEG
- PNG
- GIF
- WebP
- BMP
- TIFF

**Max file size:** 10MB

---

## Example Response

```json
{
  "success": true,
  "text": "Hello, World!",
  "confidence": 0.95,
  "processing_time_ms": 1234,
  "ocr_engine": "cloud_vision",
  "cached": false
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 401 | Invalid or missing API key |
| 400 | Invalid file type or corrupted image |
| 413 | File too large (>10MB) |
| 422 | No file uploaded |
| 429 | Rate limit exceeded (wait and retry) |

---

## Rate Limits

- Single image: 60 requests/minute
- Batch: 10 requests/minute

---

## Need Help?

Check the full documentation at `/docs` or contact the API provider.
