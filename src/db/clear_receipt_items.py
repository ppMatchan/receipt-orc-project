from src.db.dynamodb_client import get_dynamodb_resource

dynamodb = get_dynamodb_resource()

table = dynamodb.Table("receipt_items")

# DynamoDB のレシートのアイテムテーブルを全件削除するスクリプト
def clear_receipt_items():
    response = table.scan(
        ProjectionExpression="item_id"
    )

    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ProjectionExpression="item_id",
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    print(f"Delete target count: {len(items)}")

    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(
                Key={
                    "item_id": item["item_id"]
                }
            )

    print("ReceiptItems cleared.")


if __name__ == "__main__":
    clear_receipt_items()