import json
import boto3
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-1")
table = dynamodb.Table("receipt_items")

items = []
response = table.scan()
items.extend(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    items.extend(response.get("Items", []))

with open("result.json", "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)

print(f"Exported {len(items)} items to result.json")