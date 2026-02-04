# OCR API - Terminal Commands

All the commands you need to run and test the OCR API.

---

## Quick Test Commands

### Single Image OCR
```bash
curl -X POST -F "image=@tests/sample_images/text_sample.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

### Batch OCR (Multiple Images)
```bash
curl -X POST \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/test.png" \
  -F "images=@tests/sample_images/small.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/extract-text/batch
```

### Health Check
```bash
curl https://ocr-service-243539984009.us-central1.run.app/health
```

### API Info
```bash
curl https://ocr-service-243539984009.us-central1.run.app/
```

---

## Test Each Sample Image

```bash
# Standard text sample
curl -X POST -F "image=@tests/sample_images/text_sample.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text

# High quality image
curl -X POST -F "image=@tests/sample_images/high_quality.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text

# Low quality image (tests preprocessing)
curl -X POST -F "image=@tests/sample_images/low_quality.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text

# Rotated text
curl -X POST -F "image=@tests/sample_images/rotated.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text

# Invoice
curl -X POST -F "image=@tests/sample_images/invoice.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text

# Small image (tests upscaling)
curl -X POST -F "image=@tests/sample_images/small.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text

# PNG format
curl -X POST -F "image=@tests/sample_images/test.png" https://ocr-service-243539984009.us-central1.run.app/extract-text

# No text (edge case)
curl -X POST -F "image=@tests/sample_images/no_text.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

---

## Pretty Print JSON Output

Add `| python3 -m json.tool` to format the JSON response:

```bash
curl -s -X POST -F "image=@tests/sample_images/text_sample.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text | python3 -m json.tool
```

Or use `jq` if installed:
```bash
curl -s -X POST -F "image=@tests/sample_images/text_sample.jpg" https://ocr-service-243539984009.us-central1.run.app/extract-text | jq
```

---

## Local Development

### Install Dependencies
```bash
cd "/Users/arnobrizwan/Api Test"
pip install -r requirements.txt
```

### Run Locally
```bash
uvicorn app.main:app --reload --port 8080
```

### Test Local Server
```bash
curl -X POST -F "image=@tests/sample_images/text_sample.jpg" http://localhost:8080/extract-text
```

### Run Tests
```bash
pytest tests/ -v
```

---

## Docker Commands

### Build Docker Image
```bash
docker build -t ocr-api .
```

### Run Docker Container
```bash
docker run -p 8080:8080 -e GOOGLE_APPLICATION_CREDENTIALS=/creds/key.json -v ~/.config/gcloud:/creds ocr-api
```

### Test Docker Container
```bash
curl -X POST -F "image=@tests/sample_images/text_sample.jpg" http://localhost:8080/extract-text
```

---

## Google Cloud Deployment

### Set Project
```bash
gcloud config set project ocr-api-arnob-2024
```

### Build and Push to Artifact Registry
```bash
cd "/Users/arnobrizwan/Api Test"
gcloud builds submit --tag us-central1-docker.pkg.dev/ocr-api-arnob-2024/ocr-api/ocr-service:latest
```

### Deploy to Cloud Run
```bash
gcloud run deploy ocr-service \
  --image us-central1-docker.pkg.dev/ocr-api-arnob-2024/ocr-api/ocr-service:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 60
```

### View Cloud Run Logs
```bash
gcloud run services logs read ocr-service --region us-central1 --limit 50
```

### Get Service URL
```bash
gcloud run services describe ocr-service --region us-central1 --format="value(status.url)"
```

---

## Useful GCloud Commands

### Check Current Project
```bash
gcloud config get-value project
```

### List All Services
```bash
gcloud run services list
```

### View Service Details
```bash
gcloud run services describe ocr-service --region us-central1
```

### Delete Service (if needed)
```bash
gcloud run services delete ocr-service --region us-central1
```

---

## Test Error Cases

### Invalid File Type
```bash
curl -X POST -F "image=@README.md" https://ocr-service-243539984009.us-central1.run.app/extract-text
```

### Missing File
```bash
curl -X POST https://ocr-service-243539984009.us-central1.run.app/extract-text
```

---

## Interactive API Documentation

### Swagger UI
```bash
open https://ocr-service-243539984009.us-central1.run.app/docs
```

### ReDoc
```bash
open https://ocr-service-243539984009.us-central1.run.app/redoc
```

---

## One-Liner Test All Sample Images

```bash
for img in tests/sample_images/*; do echo "=== Testing: $img ===" && curl -s -X POST -F "image=@$img" https://ocr-service-243539984009.us-central1.run.app/extract-text | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Text: {d[\"text\"][:50]}... | Confidence: {d[\"confidence\"]}')" 2>/dev/null || echo "Failed"; done
```
