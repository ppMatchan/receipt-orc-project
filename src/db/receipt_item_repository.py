from datetime import datetime
import os
from uuid import uuid4

from src.db.dynamodb_client import get_dynamodb_resource

RECEIPT_ITEMS_TABLE_NAME = os.getenv("RECEIPT_ITEMS_TABLE_NAME", "receipt_items")

# DynamoDBのreceipt_itemsテーブルデータを保存するためのリポジトリクラス
class ReceiptItemRepository:
    def __init__(self):
        dynamodb = get_dynamodb_resource()
        self.table = dynamodb.Table(RECEIPT_ITEMS_TABLE_NAME)

    def put_item(self, item: dict) -> dict:
        item_to_save = {
            "item_id": str(uuid4()),
            "name": item["name"],
            "price": item["price"],
            "category_id": item.get("category_id", "unknown"),
            "category_name": item.get("category_name", "未分類"),
            "matched_keyword": item.get("matched_keyword"),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        if "purchase_datetime" in item:
            item_to_save["purchase_datetime"] = item["purchase_datetime"]

        self.table.put_item(Item=item_to_save)
        return item_to_save

    def put_items(self, items: list[dict]) -> list[dict]:
        saved_items = []

        for item in items:
            saved_item = self.put_item(item)
            saved_items.append(saved_item)

        return saved_items