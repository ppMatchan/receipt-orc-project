from pathlib import Path
import sys

# プロジェクトのルートディレクトリを sys.path に追加
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from src.db.dynamodb_client import get_dynamodb_resource


TABLE_NAME = "category_master"
CATEGORY_ID = "health_care"
NEW_KEYWORDS = ["めぐ リズム"]

# 手動でカテゴリにキーワードを追加するためのスクリプト
def main():
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(TABLE_NAME)

    response = table.get_item(
        Key={
            "category_id": CATEGORY_ID
        }
    )

    item = response.get("Item")

    if not item:
        raise Exception(f"Category not found: {CATEGORY_ID}")

    keywords = item.get("keywords", [])

    # DynamoDB から取得した keywords が set の場合は list に変換
    if isinstance(keywords, set):
        keywords = list(keywords)

    added = []

    for keyword in NEW_KEYWORDS:
        if keyword not in keywords:
            keywords.append(keyword)
            added.append(keyword)

    if not added:
        print("No new keyword added. Already exists.")
        print("keywords:", keywords)
        return

    table.update_item(
        Key={
            "category_id": CATEGORY_ID
        },
        UpdateExpression="SET #keywords = :keywords",
        ExpressionAttributeNames={
            "#keywords": "keywords"
        },
        ExpressionAttributeValues={
            ":keywords": keywords
        }
    )

    print("Added keywords:", added)
    print("Updated keywords:", keywords)


if __name__ == "__main__":
    main()