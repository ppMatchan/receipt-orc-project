from src.db.dynamodb_client import get_dynamodb_resource

dynamodb = get_dynamodb_resource()

table = dynamodb.Table("category_master")


def scan_all_categories():
    response = table.scan()
    items = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    return items


def search_keyword(keyword: str):
    items = scan_all_categories()

    found = []

    for item in items:
        keywords = item.get("keywords", [])

        if keyword in keywords:
            found.append(item)

    return found


if __name__ == "__main__":
    # keyword = "さかな"

    # result = search_keyword(keyword)

    # if result:
    #     print(f"Found keyword: {keyword}")
    #     for item in result:
    #         print(item)
    # else:
    #     print(f"Not found keyword: {keyword}")

    items = scan_all_categories()

    for item in items:
        print(item)