from src.db.category_repository import CategoryRepository


class ClassifyProduct:

    def __init__(self):
       self.category_repository = CategoryRepository()

    def classify(self, item_name: str) -> dict:
        """
        商品名からカテゴリを判定する

        return example:
        {
            "category_id": "food",
            "category_name": "食費",
            "matched_keyword": "たまご"
        }
        """

        categories = self.category_repository.get_all_categories()
        normalized_item_name = self._normalize_text(item_name)

        for category in categories:
            category_id = category.get("category_id")
            category_name = category.get("category_name")
            keywords = category.get("keywords", [])

            # unknown は最後の fallback 用なので keyword 判定対象から外す
            if category_id == "unknown":
                continue

            for keyword in keywords:
                normalized_keyword = self._normalize_text(keyword)

                if normalized_keyword in normalized_item_name:
                    return {
                        "category_id": category_id,
                        "category_name": category_name,
                        "matched_keyword": keyword,
                    }

        return {
            "category_id": "unknown",
            "category_name": "未分類",
            "matched_keyword": None,
        } 
    
    def classify_items(self, items: list[dict]) -> list[dict]:
        """
        parser 済みの商品リストにカテゴリを付ける

        input example:
        [
            {"name": "サイズ ミックス たまご", "price": 258},
            {"name": "プレミアム ガーナ 芳醇 カカ", "price": 318}
        ]

        output example:
        [
            {
                "name": "サイズ ミックス たまご",
                "price": 258,
                "category_id": "food",
                "category_name": "食費",
                "matched_keyword": "たまご"
            }
        ]
        """

        classified_items = []

        for item in items:
            item_name = item.get("name", "")
            category = self.classify(item_name)

            classified_items.append({
                **item,
                "category_id": category["category_id"],
                "category_name": category["category_name"],
                "matched_keyword": category["matched_keyword"],
            })

        return classified_items

    
    def _normalize_text(self, text: str) -> str:
        """
        OCR結果のスペース差異を吸収するための正規化
        """
        if text is None:
            return ""

        return str(text).replace(" ", "").replace("　", "").lower() 