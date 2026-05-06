from src.db.category_repository import CategoryRepository


repo = CategoryRepository()

repo.put_category("たまご", "food")
repo.put_category("キャベツ", "food")
repo.put_category("ガーナ", "snack")
repo.put_category("受付", "none")
repo.put_category("パートナー", "none")

item = repo.get_category("たまご")
print(item)

all_items = repo.scan_all_categories()
print(all_items)