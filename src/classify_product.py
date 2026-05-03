import re

from rapidfuzz import fuzz, process
import json
from pathlib import Path

class ClassifyProduct:

    #DISCOUNT_PATTERNS = ["割引", "値引", "引", "OFF", "オフ", "ディスカウント", "特価", "セール","値下げ","値下"]

    #TEL_KEYWORDS = ["TEL", "電話", "電話番号", "連絡先", "お問い合わせ"]

    def __init__(self):
        self.SUMMARY_PATTERNS = self.load_keywords("summary_keywords.json")
        self.DISCOUNT_PATTERNS = self.load_keywords("discount_keywords.json").get("discount_keywords", [])
        self.NON_ITEM_MASTER = self.load_keywords("non_item_keywords.json")
    
    def load_keywords(self, file_name=""):
        if not file_name:
            return ""
        base_dir = Path(__file__).resolve().parent.parent
        file_path = base_dir / "data" / file_name

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    # แยกสินค้ากับสรุปยอดจากรายการที่แยกได้
    def classify_items(self, parsed_items):
        items = []
        summary = {}

        for item in parsed_items:
            name = item['name']
            price = item['price']

            # ตรวจสอบว่าบรรทัดนั้นเป็นบรรทัดที่ไม่ใช่สินค้า (เช่น บรรทัดที่มีคำว่า "領収証" หรือ "レシート") โดยใช้ NON_ITEM_KEYWORDS
            if self.is_non_item_line(name):
                continue

            if self.is_discount_line(name):
                # หากเป็นบรรทัดส่วนลด ให้หักส่วนลดจากสินค้าก่อนหน้า ถ้าไม่มีสินค้าก่อนหน้าให้เก็บไว้ใน summary แทน
                if items:
                    discount_amount = abs(price)
                    items[-1]["price"] -= discount_amount
                    items[-1]["discount"] = items[-1].get("discount", 0) + discount_amount
                else:
                    summary.setdefault("discounts", []).append(item)
                continue
            
            # ตรวจสอบว่าบรรทัดนั้นเป็นบรรทัดสรุปยอดหรือไม่ โดยดูจากการมีคำที่บ่งบอกสรุปยอดและไม่มีคำที่บ่งบอกหมายเลขโทรศัพท์
            key, score = self.detect_summary_key(name)

            # หากเป็นบรรทัดสรุปยอด ให้เก็บไว้ใน summary แทนที่จะเก็บเป็นสินค้า
            if key:
               summary[key] = price
               print(f"SUMMARY detected: {key}, score={score}, text={name}")
            else:
                items.append(item)

        return items, summary
    
    # ทำความสะอาดข้อความโดยการลบช่องว่างและแปลงสัญลักษณ์ที่คล้ายกันให้เหมือนกัน เพื่อช่วยในการตรวจสอบ pattern ต่าง ๆ ได้แม่นยำขึ้น
    def normalize_text(self,text):
        return (
            text.replace(" ", "")
                .replace("　", "")
                .replace("\\", "¥")
                .replace("￥", "¥")
        )
    
    # ตรวจสอบว่าบรรทัดนั้นเป็นบรรทัดส่วนลดหรือไม่ โดยดูจากการมีคำที่บ่งบอกส่วนลด
    def is_discount_line(self, text):
        text = self.normalize_text(text)
        # return any(pattern in text for pattern in self.DISCOUNT_PATTERNS) and not any(tel_keyword in text for tel_keyword in self.TEL_KEYWORDS)
        return any(pattern in text for pattern in self.DISCOUNT_PATTERNS) 
    
    def is_non_item_line(self, text):
        compact = text.replace(" ", "").replace("　", "")

        # keyword check
        for keyword in self.NON_ITEM_MASTER["non_item_keywords"]:
            if keyword in compact:
                return True

        # regex check
        for pattern in self.NON_ITEM_MASTER["non_item_regex_patterns"]:
            if re.search(pattern, text):
                return True

        return False
    
    # ตรวจสอบว่าบรรทัดนั้นเป็นบรรทัดสรุปยอดหรือไม่ โดยดูจากการมีคำที่บ่งบอกสรุปยอด
    def detect_summary_key(self, text, threshold=75):
        text = self.normalize_text(text)

        best_key = None
        best_score = 0

        for key, patterns in self.SUMMARY_PATTERNS.items():
            result = process.extractOne(
                text,
                patterns,
                scorer=fuzz.partial_ratio
            )

            if result:
                pattern, score, _ = result
                if score > best_score:
                    best_key = key
                    best_score = score

        if best_score >= threshold:
            return best_key, best_score

        return None, best_score
    
    # global function to check if a line is summary line (called from ocr.py) โดยใช้ detect_summary_key 
    def is_summary_line(self, text):
        key, score = self.detect_summary_key(text)
        return key is not None