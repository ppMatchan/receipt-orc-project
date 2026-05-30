import json
from pathlib import Path

from src.db.category_repository import CategoryRepository

# カテゴリーマスターテーブルに初期データを投入するスクリプト
def seed_category_master():
    base_dir = Path(__file__).resolve().parents[2]
    json_path = base_dir / "data" / "categories_master.json"

    repo = CategoryRepository()

    with open(json_path, "r", encoding="utf-8") as f:
        categories = json.load(f)

    for category in categories:
        repo.put_category(category)
        print(f"seeded: {category['category_id']}")

    print("category master seed completed.")


if __name__ == "__main__":
    seed_category_master()