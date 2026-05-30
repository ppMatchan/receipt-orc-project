import boto3
import os

def get_dynamodb_resource():
    """
    Local DynamoDB 用。
    ตอนขึ้น AWS จริง ให้ไม่ใส่ endpoint_url
    """
    # endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8000")
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
    region_name = os.getenv("AWS_REGION", "ap-northeast-1")
    
    if endpoint_url:
        # DynamoDB Local を使用する場合
        return boto3.resource(
            "dynamodb",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "dummy"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "dummy"),
        )
    else:
        # AWS 上の DynamoDB を使用する場合
        return boto3.resource(
            "dynamodb",
            region_name=region_name,
        )