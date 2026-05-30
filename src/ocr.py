
import json
import os
import boto3
from google.cloud import vision
from google.oauth2 import service_account


class OcrProcessor:
    def __init__(self):
        return
        
    def create_vision_client(self):
        """Google Vision APIのクライアントを作成するメソッド。AWS Secrets Managerから認証情報を取得してクライアントを初期化する。"""

        secret_name = os.environ.get("GOOGLE_VISION_SECRET_NAME")
        region_name = os.environ.get("AWS_REGION", "ap-northeast-1")

        if not secret_name:
            raise ValueError("GOOGLE_VISION_SECRET_NAME is not set")

        secret_client = boto3.client("secretsmanager", region_name=region_name)
        response = secret_client.get_secret_value(SecretId=secret_name)

        secret_dict = json.loads(response["SecretString"])

        credentials = service_account.Credentials.from_service_account_info(
            secret_dict
        )

        return vision.ImageAnnotatorClient(credentials=credentials)
    
    def text_ocr(self, image_path: str):
        """ 画像からテキストを抽出するメソッド。Google Vision APIを使用して、画像内のテキストを検出し、抽出されたテキストを返す。"""
        
        client = self.create_vision_client()

        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(response.error.message)
        
        full_text = response.full_text_annotation.text

        print("===== FULL TEXT =====")
        print(full_text)

        return response

