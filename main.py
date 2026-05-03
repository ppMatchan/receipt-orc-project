from src.ocr import OcrProcessor
from src.parser import ParseTextToLine
from src.classify_product import ClassifyProduct
from src.arrange_text import ArrangeTextPosition
from src.preprocess_img import ReceiptImagePreprocessor

def main(image_file):
    image_raw_path = "pics/raw_pics/"
    image_processed_path = "pics/processed_pics/"
    processor = ReceiptImagePreprocessor()
    ocrObj = OcrProcessor()
    arrangeText = ArrangeTextPosition()
    classifyProduct = ClassifyProduct()
    parseText = ParseTextToLine()
    
    # preprocess image (e.g. binarization, noise reduction)
    processor.preprocess(
        image_raw_path + image_file,
        image_processed_path + "rotated_" + image_file
    )

    processor.sharpen_threshold(
        image_processed_path + "rotated_" + image_file,
        image_processed_path + "bold_" + image_file
    )

    # google vision API call
    response = ocrObj.text_ocr(image_processed_path + "bold_" + image_file)

    lines = arrangeText.get_text_by_lines(response)
    print("===== LINE =====")
    print("\n".join(lines))

    
    receipt_lines = parseText.parse_receipt_lines(lines)

    items, summary = classifyProduct.classify_items(receipt_lines)

    print("===== ITEMS =====")
    for item in items:
        print(f"Item: {item['name']}, Price: {item['price']}")

    print("\n===== SUMMARY =====")
    for key, value in summary.items():
        print(f"{key.capitalize()}: {value}")


if __name__ == "__main__":
    main("receipt3.jpg")