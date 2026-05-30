# Receipt OCR & Expense Categorization Project
Japanese receipt OCR application that extracts item names and prices from receipt images,  
categorizes each item, and stores the result in DynamoDB for monthly expense visualization.  
This project was created as a portfolio project to practice AWS serverless architecture,  
OCR processing, Docker-based Lambda deployment, and DynamoDB data design.

## Overview
This application processes Japanese receipt images and performs the following steps:

1. Upload a receipt image
2. Preprocess the image to improve OCR accuracy
3. Extract text using Google Cloud Vision API
4. Parse receipt information such as purchase date, item names, prices, subtotal, tax, and total
5. Categorize each item using category master data
6. Save the result to Amazon DynamoDB
7. Display monthly expense summaries in pie chart through a web page

## Architecture
``` text
Upload receipt Image  
    ↓  
Amazon S3  
    ↓  
AWS Lambda (Container Image)  
    ↓  
Google Cloud Vision API  
    ↓  
Parser / Categorizer  
    ↓  
Amazon DynamoDB  
    ↓  
API Gateway + Lambda  
    ↓  
Static Web Page on S3
```

## Tech Stack

### Backend
* Python
* AWS Lambda
* Amazon S3
* Amazon DynamoDB
* Amazon ECR
* Docker
* Google Cloud Vision API
* boto3
* OpenCV
* Pillow

### Frontend
* HTML
* CSS
* JavaScript
* Chart.js
* Amazon S3 Static Website Hosting

## Main Features
* Japanese receipt OCR using Google Cloud Vision API
* Image preprocessing before OCR
* Item and price extraction from receipt text
* Purchase date extraction
* Item categorization using category master data
* DynamoDB storage
* Monthly category-based expense visualization
* Serverless deployment using AWS Lambda container image

## Project Structure
``` text
├── src/  
│ ├── ocr.py  
│ ├── parser.py  
│ ├── preprocess_img.py  
│ ├── receipt_pipeline.py  
│ ├── classify_product.py  
│ └── db/  
│       ├── dynamodb_client.py  
│       ├── category_repository.py  
│       └── receipt_repository.py  
├── data/  
│       ├── discount_keywords.py  
│       ├── non_item_keywords.py  
│       └── summary_keywords.json  
├── lambda_handler.py  
├── requirements.txt  
├── Dockerfile  
└── README.md  
```

## Local Development
1. Create virtual environment
> python -m venv .venv
2. Activate virtual environment
> .venv\Scripts\activate
3. Install dependencies
> pip install -r requirements.txt
4. Run local test
> python main.py

### DynamoDB Local
This project uses DynamoDB Local during development.

> docker run -p 8000:8000 amazon/dynamodb-local

After starting DynamoDB Local, create and seed the required tables.

> python -m src.db.create_tables  
> python -m src.db.seed_category_master

## AWS Deployment
 
 This project is deployed to AWS Lambda using a container image.

## AWS Services Used
* __Amazon S3__: receipt image storage and static web hosting
* __AWS Lambda__: OCR and data processing
* __Amazon ECR__: Lambda container image repository
* __Amazon DynamoDB__: receipt item storage and category master data
* __AWS Secrets Manager__: Google Cloud Vision credential management
* __Amazon API Gateway__: API endpoint for result retrieval
* __Amazon CloudWatch Logs__: monitoring and debugging

## Future Improvements
* Improve OCR accuracy for difficult receipt layouts
* Add AI-based category suggestion for unknown items
* Add user upload screen
* Add authentication
* Improve UI design
* Add monthly and yearly expense reports
* Add automated reclassification for unknown items