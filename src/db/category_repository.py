from src.db.dynamodb_client import get_dynamodb_resource


CATEGORY_TABLE_NAME = "category_master"


class CategoryRepository:
    def __init__(self):
        dynamodb = get_dynamodb_resource()
        self.table = dynamodb.Table(CATEGORY_TABLE_NAME)

    def get_all_categories(self) -> list[dict]:
        response = self.table.scan()
        return response.get("Items", [])

    def get_category(self, category_id: str) -> dict | None:
        response = self.table.get_item(
            Key={
                "category_id": category_id
            }
        )
        return response.get("Item")

    def put_category(self, category: dict) -> None:
        self.table.put_item(Item=category)

    def add_keyword_to_category(self, category_id: str, keyword: str) -> None:
        category = self.get_category(category_id)

        if not category:
            raise ValueError(f"Category not found: {category_id}")

        keywords = category.get("keywords", [])

        if keyword not in keywords:
            keywords.append(keyword)

        category["keywords"] = keywords
        self.put_category(category)