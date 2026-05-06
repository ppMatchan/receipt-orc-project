

from pathlib import Path

from src.preprocess_img import ReceiptImagePreprocessor
from src.ocr import OcrProcessor
from src.parser import ParseTextToLine
from src.classify_product import ClassifyProduct
from src.arrange_text import ArrangeTextPosition
from src.db.receipt_item_repository import ReceiptItemRepository

class ReceiptPipeline:
    def __init__(self, processed_dir: str):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.processor = ReceiptImagePreprocessor()
        self.ocr = OcrProcessor()
        self.parser = ParseTextToLine()
        self.category_service = ClassifyProduct()
        self.repository = ArrangeTextPosition()
        self.db_repository = ReceiptItemRepository()


    def run(self, image_path: str):
        # Preprocess the image        
        processed_image_path = self.processor.preprocess(image_path, self.processed_dir)

        # Perform OCR
        ocr_response = self.ocr.text_ocr(str(processed_image_path))

        # Arrange text by lines
        lines = self.repository.get_text_by_lines(ocr_response)
        print("===== LINE =====")
        for line in lines:
            print(line)

        # Parse lines into structured receipt data
        receipt_data = self.parser.parse_receipt_lines(lines)
        print("===== PARSED RECEIPT DATA =====")
        print(receipt_data)

        # Classify products and extract summary
        classified_items = self.category_service.classify_items(receipt_data['items'])
        print("===== CLASSIFIED ITEMS =====")
        for item in classified_items:
            print(item)

        # save to db
        items_to_save = []
        receipt_datetime = receipt_data["datetime"]

        for item in classified_items:
            item_to_save = {
                "name": item["name"],
                "price": item["price"],
                "category_id": item["category_id"],
                "category_name": item["category_name"],
                "matched_keyword": item["matched_keyword"],
                "purchase_datetime": receipt_datetime.isoformat(),
                "image_path": str(image_path)
            }
            items_to_save.append(item_to_save)

        saved_items = self.db_repository.put_items(items_to_save)

        return saved_items