# OCR API - Terminal Commands

All the commands you need to run and test the OCR API.

---

## Setup (Run These First!)

```bash
# Set the API URL
export OCR_API_URL="https://ocr-service-243539984009.us-central1.run.app"

# Set your API Key
export OCR_API_KEY="OCR_Secret_2026"
```

---

## Quick Test Commands

### Health Check (No Auth Required)
```bash
curl $OCR_API_URL/health
```

### API Info (No Auth Required)
```bash
curl $OCR_API_URL/
```

### Single Image OCR
```bash
curl -X POST \
  -H "X-API-Key: $OCR_API_KEY" \
  -F "image=@tests/sample_images/text_sample.jpg" \
  $OCR_API_URL/v1/extract-text
```

### Batch OCR (Multiple Images)
```bash
curl -X POST \
  -H "X-API-Key: $OCR_API_KEY" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/test.png" \
  -F "images=@tests/sample_images/small.jpg" \
  $OCR_API_URL/v1/extract-text/batch
```

### Cache Statistics
```bash
curl -H "X-API-Key: $OCR_API_KEY" $OCR_API_URL/v1/cache/stats
```

### Clear Cache
```bash
curl -X DELETE -H "X-API-Key: $OCR_API_KEY" $OCR_API_URL/v1/cache
```

---

## Test Each Sample Image

```bash
# Standard text sample
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/text_sample.jpg" $OCR_API_URL/v1/extract-text

# High quality image
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/high_quality.jpg" $OCR_API_URL/v1/extract-text

# Low quality image (tests preprocessing)
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/low_quality.jpg" $OCR_API_URL/v1/extract-text

# Rotated text
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/rotated.jpg" $OCR_API_URL/v1/extract-text

# Invoice
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/invoice.jpg" $OCR_API_URL/v1/extract-text

# Small image
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/small.jpg" $OCR_API_URL/v1/extract-text

# PNG format
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/test.png" $OCR_API_URL/v1/extract-text

# No text (edge case)
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/no_text.jpg" $OCR_API_URL/v1/extract-text
```

---

## Pretty Print JSON Output

Add `| python3 -m json.tool` to format the JSON response:

```bash
curl -s -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/text_sample.jpg" $OCR_API_URL/v1/extract-text | python3 -m json.tool
```

Or use `jq` if installed:
```bash
curl -s -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/text_sample.jpg" $OCR_API_URL/v1/extract-text | jq
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
export OCR_API_URL="http://localhost:8080"
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/text_sample.jpg" $OCR_API_URL/v1/extract-text
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
docker run -p 8080:8080 \
  -e API_KEY=$OCR_API_KEY \
  -e GOOGLE_APPLICATION_CREDENTIALS=/creds/key.json \
  -v ~/.config/gcloud:/creds \
  ocr-api
```

### Test Docker Container
```bash
export OCR_API_URL="http://localhost:8080"
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@tests/sample_images/text_sample.jpg" $OCR_API_URL/v1/extract-text
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
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --min-instances 1
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

## Test Error Cases

### Invalid File Type
```bash
curl -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@README.md" $OCR_API_URL/v1/extract-text
```

### Missing File
```bash
curl -X POST -H "X-API-Key: $OCR_API_KEY" $OCR_API_URL/v1/extract-text
```

### Missing API Key (should fail)
```bash
curl -X POST -F "image=@tests/sample_images/text_sample.jpg" $OCR_API_URL/v1/extract-text
```

### Too Many Files in Batch (>10)
```bash
curl -X POST -H "X-API-Key: $OCR_API_KEY" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  $OCR_API_URL/v1/extract-text/batch
```

---

## Interactive Documentation

### Swagger UI
```bash
open $OCR_API_URL/docs
```

### ReDoc
```bash
open $OCR_API_URL/redoc
```

### Web Dashboard
```bash
open $OCR_API_URL/web
```

---

## One-Liner Test All Sample Images

```bash
for img in tests/sample_images/*; do echo "=== Testing: $img ===" && curl -s -X POST -H "X-API-Key: $OCR_API_KEY" -F "image=@$img" $OCR_API_URL/v1/extract-text | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Text: {d.get(\"text\", \"N/A\")[:50]}... | Confidence: {d.get(\"confidence\", \"N/A\")}')" 2>/dev/null || echo "Failed"; done
```

---

## Copy-Paste Ready (Full URLs)

If you don't want to set environment variables, use these directly:

### Single Image
```bash
curl -X POST \
  -H "X-API-Key: OCR_Secret_2026" \
  -F "image=@tests/sample_images/text_sample.jpg" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text
```

### Batch
```bash
curl -X POST \
  -H "X-API-Key: OCR_Secret_2026" \
  -F "images=@tests/sample_images/text_sample.jpg" \
  -F "images=@tests/sample_images/test.png" \
  https://ocr-service-243539984009.us-central1.run.app/v1/extract-text/batch
```

### Health Check
```bash
curl https://ocr-service-243539984009.us-central1.run.app/health
```

### Cache Stats
```bash
curl -H "X-API-Key: OCR_Secret_2026" https://ocr-service-243539984009.us-central1.run.app/v1/cache/stats
```
