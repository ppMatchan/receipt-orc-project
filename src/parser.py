import re
from src.classify_product import ClassifyProduct

class ParseTextToLine:
    def __init__(self):
        pass
    
    def is_phone_line(self, text):
        return (
            "TEL" in text
            or re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", text)
        )
    
    def normalize_price_text(self, text: str) -> str:
        # ¥ 4 , 980 -> ¥ 4,980
        text = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', text)

        # 4 , 980 -> 4,980
        text = re.sub(r'\s+', ' ', text)

        return text

    def extract_price(self, text, allow_plain_number=False):
        
        # check if line contains phone number → skip
        if self.is_phone_line(text):
            return None
        
        # normalize price text to handle cases like "¥ 4 , 980" or "4 , 980"
        text = self.normalize_price_text(text)

        # 1. discount for example : -80
        minus_matches = re.findall(r"[-−]\s*[\d,\.]+", text)
        if minus_matches:
            raw = minus_matches[-1]
            raw = re.sub(r"[-−\s,\.]", "", raw)
            return -int(raw)

        # 2. price with symbol for example : ¥128, \ 1.370
        price_matches = re.findall(r"[¥￥\\]\s*\d[\d,\.\s]*", text)
        if price_matches:
            raw = price_matches[-1]
            raw = re.sub(r"[¥￥\\\s,\.]", "", raw)
            if raw.isdigit():
                return int(raw)

           # 2. price without symbol at end of line: フジンサイフ 4,980
        price_matches = re.findall(r"\d{1,3}(?:[,.]\d{3})+|\d+", text)

        if price_matches:
            raw = price_matches[-1]
            raw = re.sub(r"[,\.]", "", raw)

            if raw.isdigit():
                return int(raw)
            
        # 3. fallback: summary for example : 合計 / 6 点 * 1.479
        if allow_plain_number:
            nums = re.findall(r"\d[\d,\.]*", text)
            if nums:
                raw = nums[-1]   # 6 and 1.479 → take 1.479
                raw = raw.replace(",", "").replace(".", "")
                return int(raw)

        return None

    def normalize_price(self, price_text):
        # get only digits, comma, and dot
        cleaned = re.sub(r"[^\d,\.]", "", price_text)

        # if both , and . → assume . is noise
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "")

        # if only . → treat as thousand separator (Japan doesn't use decimal)
        elif "." in cleaned:
            cleaned = cleaned.replace(".", "")

        # remove comma
        cleaned = cleaned.replace(",", "")

        return int(cleaned)


    def remove_amount_from_text(self, text):
        # ลบ ¥128, ￥128, \ 1.370
        text = re.sub(r"[¥￥\\]\s*[\d,\.]+", "", text)

        # ลบจำนวนเงินที่เหลืออยู่
        # text = re.sub(r"\d{1,3}(?:[,.]\d{3})+|\d+", "", text)

        # ลบ -80 หรือ −80 (discount)
        text = re.sub(r"[-−]\s*[\d,\.]+", "", text)

        # ลบ % เช่น 20 %
        text = re.sub(r"\d+\s*%", "", text)

        # ลบช่องว่างซ้ำ
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def parse_receipt_lines(self, lines):
        receipt_lines = []
        classifyProduct = ClassifyProduct()

        for line in lines:
            line = line.strip()
            is_allow_plain_number = classifyProduct.is_summary_line(line)
            
            price = self.extract_price(line, allow_plain_number=is_allow_plain_number)
            print(f"Extracted price: {price} from line: {line}")

            if price is None:
                continue

            name = self.remove_amount_from_text(line)

            receipt_lines.append({
                "name": name,
                "price": price
            })

        return receipt_lines
