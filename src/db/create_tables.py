from botocore.exceptions import ClientError
from src.db.dynamodb_client import get_dynamodb_resource

CATEGORY_MASTER_TABLE_NAME = "category_master"
RECEIPT_ITEMS_TABLE_NAME = "receipt_items"

def create_category_master_table():
    dynamodb = get_dynamodb_resource()

    try:
        table = dynamodb.create_table(
            TableName=CATEGORY_MASTER_TABLE_NAME,
            KeySchema=[
                {
                    "AttributeName": "category_id",
                    "KeyType": "HASH",
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "category_id",
                    "AttributeType": "S",
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        table.wait_until_exists()
        print("category_master table created.")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("category_master table already exists.")
        else:
            raise

def create_receipt_items_table():
    dynamodb = get_dynamodb_resource()

    existing_tables = [table.name for table in dynamodb.tables.all()]
    if RECEIPT_ITEMS_TABLE_NAME in existing_tables:
        print(f"{RECEIPT_ITEMS_TABLE_NAME} table already exists.")
        return

    table = dynamodb.create_table(
        TableName=RECEIPT_ITEMS_TABLE_NAME,
        KeySchema=[
            {
                "AttributeName": "item_id",
                "KeyType": "HASH",
            }
        ],
        AttributeDefinitions=[
            {
                "AttributeName": "item_id",
                "AttributeType": "S",
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    table.wait_until_exists()
    print(f"{RECEIPT_ITEMS_TABLE_NAME} table created.")
    
if __name__ == "__main__":
    create_category_master_table()
    create_receipt_items_table()