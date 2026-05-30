import json
import os
from decimal import Decimal
from collections import defaultdict

import boto3
from boto3.dynamodb.conditions import Attr


TABLE_NAME = os.getenv("RECEIPT_ITEMS_TABLE", "receipt_items")
REGION_NAME = os.getenv("AWS_REGION", "ap-northeast-1")


dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
table = dynamodb.Table(TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super().default(obj)


def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters") or {}

        year = params.get("year")
        month = params.get("month")

        if not year or not month:
            return response(400, {
                "message": "year and month are required. Example: ?year=2026&month=05"
            })

        month = month.zfill(2)
        target_prefix = f"{year}-{month}"

        # MVP: DynamoDBのScanで対象月のデータを全件取得してから集計する → データ量が増えたらクエリベースに切り替える
        # purchase_datetime 例: 2026-05-01T17:36:00
        scan_param = {
            "FilterExpression": Attr("purchase_datetime").begins_with(target_prefix)
        }

        items = []
        while True:
            result = table.scan(**scan_param)
            items.extend(result.get("Items", []))

            if "LastEvaluatedKey" not in result:
                break

            scan_param["ExclusiveStartKey"] = result["LastEvaluatedKey"]

        category_totals = defaultdict(lambda: {
            "category_id": "",
            "category_name": "",
            "total": 0
        })

        for item in items:
            category_id = item.get("category_id", "unknown")
            category_name = item.get("category_name", "未分類")
            price = int(item.get("price", 0))

            category_totals[category_id]["category_id"] = category_id
            category_totals[category_id]["category_name"] = category_name
            category_totals[category_id]["total"] += price

        categories = list(category_totals.values())
        categories.sort(key=lambda x: x["total"], reverse=True)

        body = {
            "year": year,
            "month": month,
            "categories": categories,
            "item_count": len(items)
        }

        return response(200, body)

    except Exception as e:
        print("ERROR:", str(e))
        return response(500, {
            "message": "Internal server error",
            "error": str(e)
        })


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS"
        },
        "body": json.dumps(body, ensure_ascii=False, cls=DecimalEncoder)
    }