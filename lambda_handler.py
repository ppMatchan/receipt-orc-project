import os
import json
import boto3
import urllib.parse

from src.receipt_pipeline import ReceiptPipeline

s3 = boto3.client("s3")

TEMP_DIR = os.getenv("TEMP_DIR", "/tmp")
RAW_DIR = os.path.join(TEMP_DIR, "raw")
PROCESSED_DIR = os.path.join(TEMP_DIR, "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def lambda_handler(event, context):
    print("EVENT:", json.dumps(event, ensure_ascii=False))

    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

    file_name = os.path.basename(key)
    local_image_path = os.path.join(RAW_DIR, file_name)

    s3.download_file(bucket, key, local_image_path)

    pipeline = ReceiptPipeline(
        processed_dir=PROCESSED_DIR
    )

    result = pipeline.run(local_image_path)
    return {
        "statusCode": 200,
        "body": json.dumps(result, ensure_ascii=False)
    }