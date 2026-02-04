OCR Image Text Extraction Cloud Run Challenge
Challenge Overview
Create a serverless API using Google Cloud Run that accepts JPG image uploads and extracts
text from them using Optical Character Recognition (OCR). This challenge tests your ability to
develop and deploy a cloud-based API that handles file uploads and integrates with image
processing services.
Requirements
1. Create an API that accepts JPG image file uploads via POST request
2. Process the uploaded image to extract any text content using OCR
3. Return the extracted text in JSON format
4. Handle cases where no text is found in the image
5. Deploy your solution to Google Cloud Run
6. Provide a public URL where your API can be accessed
7. Include proper error handling for invalid files, unsupported formats, etc.
Technical Specifications
● Input: JPG image file (multipart/form-data)
● Output: JSON response containing extracted text
● Max file size: 10MB
● Supported format: JPG/JPEG only
● Expected response format:
json

{
"success": true,
"text": "extracted text content here",
"confidence": 0.95,
"processing_time_ms": 1234
}

Deliverables
1. Public URL of your deployed Cloud Run service
2. API Documentation including:
○ HTTP method and endpoint

○ Request format (how to upload the image)
○ Response format and possible error codes
○ Example curl command for testing
3. Implementation explanation covering:
○ OCR service/library used (Google Cloud Vision API, Tesseract, etc.)
○ How you handle file uploads and validation
○ Your deployment strategy
4. GitHub repository with:
○ Complete source code
○ Dockerfile (if used)
○ README with setup instructions
○ Sample test images

Implementation Options & Recommendations
OCR Services You Can Use:
● Google Cloud Vision API (recommended for GCP integration)
● Tesseract OCR (open source, can be containerized)
● Azure Computer Vision (if you want cross-cloud experience)
● AWS Textract (though less ideal for Cloud Run)
Technology Stack Suggestions:
● Python: Flask/FastAPI + google-cloud-vision or pytesseract
● Node.js: Express + @google-cloud/vision
● Java: Spring Boot + Cloud Vision client library
● Go: Gin/Echo + Cloud Vision Go client
Free Implementation Resources
● Google Cloud Platform: Free tier includes Cloud Run and Vision API quotas
● New GCP accounts: $300 credit for 90 days
● Cloud Vision API: 1,000 units/month free
● Cloud Run: 2 million requests/month free
● Container Registry/Artifact Registry: Free tier available
Evaluation Criteria
Your submission will be evaluated on:
Functionality (40%)
● Correctly extracts text from uploaded JPG images
● Handles various image qualities and text orientations
● Proper error handling for edge cases

None
API Design (25%)
● Clean RESTful design
● Proper HTTP status codes
● Clear request/response formats
● Input validation
Deployment & Infrastructure (20%)
● Successfully deployed to Cloud Run
● Service is publicly accessible and reliable
● Proper container configuration
Code Quality (15%)
● Clean, readable, well-structured code
● Proper error handling and logging
● Security considerations (file validation, size limits)
● Performance optimization
Testing Instructions
Provide clear instructions so I can test your API like this:
bash

curl -X POST -F "image=@test_image.jpg" https://your-service-url/extract-text

Bonus Points
Consider implementing these additional features:
● Support for multiple image formats (PNG, GIF)
● Confidence scores for extracted text
● Text preprocessing (cleanup, formatting)
● Rate limiting
● Caching for identical images
● Batch processing endpoint
● Image metadata extraction
This challenge will demonstrate your ability to integrate multiple cloud services, handle file
uploads securely, and create a production-ready API that solves a real-world problem.