from email.mime import text
import json
from pathlib import Path
import re
from datetime import datetime
from rapidfuzz import fuzz, process


class ParseTextToLine:
    
    FUZZY_THRESHOLD = 80

    def __init__(self):
        self.SUMMARY_PATTERNS = self.load_keywords("summary_keywords.json")
        self.DISCOUNT_PATTERNS = self.load_keywords("discount_keywords.json").get("discount_keywords", [])
        self.NON_ITEM_MASTER = self.load_keywords("non_item_keywords.json")
    
    def load_keywords(self, file_name=""):
        """sumary_line
        description: โหลดไฟล์ JSON ที่เก็บคำหลักและรูปแบบต่าง ๆ ที่ใช้ในการตรวจสอบบรรทัดสรุปยอด บรรทัดส่วนลด และบรรทัดที่ไม่ใช่รายการสินค้า เพื่อให้สามารถปรับแต่งและเพิ่มคำหลักได้ง่ายโดยไม่ต้องแก้ไขโค้ด
        parameter file_name: ชื่อไฟล์ JSON ที่ต้องการโหลด เช่น "summary_keywords.json", "discount_keywords.json", หรือ "non_item_keywords.json"
        return: ข้อมูลที่โหลดจากไฟล์ JSON ในรูปแบบของ dictionary หรือ list ขึ้นอยู่กับโครงสร้างของไฟล์ JSON นั้น ๆ
        """
        
        if not file_name:
            return ""
        base_dir = Path(__file__).resolve().parent.parent
        file_path = base_dir / "data" / file_name

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    
    def extract_receipt_datetime(self, text: str):
        """sumary_line
        description: ดึงวันที่และเวลาจากข้อความในใบเสร็จ
        parameter text: ข้อความที่ต้องการดึงวันที่และเวลา
        return: datetime object หรือ None หากไม่พบ
        """
        
        patterns = [
            # 2016 年 04 月 19 日 ( 日 ) 10: 18
            # 2026年4月19日（日）10:18
            r"(?P<year>\d{4})\s*年\s*(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*日\s*[（(]?\s*[月火水木金土日]\s*[）)]?\s*(?P<hour>\d{1,2})\s*:\s*(?P<minute>\d{2})",

            # 2026/5/1 ( 金 ) 17:36
            # 2026 / 5 / 1 ( 金 ) 17: 36
            r"(?P<year>\d{4})\s*/\s*(?P<month>\d{1,2})\s*/\s*(?P<day>\d{1,2})\s*[（(]?\s*[月火水木金土日]\s*[）)]?\s*(?P<hour>\d{1,2})\s*:\s*(?P<minute>\d{2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                year = int(match.group("year"))
                month = int(match.group("month"))
                day = int(match.group("day"))
                hour = int(match.group("hour"))
                minute = int(match.group("minute"))

                return datetime(year, month, day, hour, minute)

        return None
    
    def normalize_text(self,text):
        """sumary_line
        description: ทำความสะอาดข้อความโดยการลบช่องว่างและแปลงสัญลักษณ์ที่คล้ายกันให้เหมือนกัน เพื่อช่วยในการตรวจสอบ pattern ต่าง ๆ ได้แม่นยำขึ้น
        parameter text: ข้อความที่ต้องการทำความสะอาด
        return: ข้อความที่ทำความสะอาดแล้ว
        """
        
        return (
            text.replace(" ", "")
                .replace("　", "")
                .replace("\\", "¥")
                .replace("￥", "¥")
        )
        
    def is_discount_line(self, text):
        """sumary_line
        description: ตรวจสอบว่าบรรทัดนั้นเป็นบรรทัดส่วนลดหรือไม่
        parameter text: line text ที่ต้องการตรวจสอบ
        return: True หากเป็นบรรทัดส่วนลด False หากไม่ใช่
        """
        
        text = self.normalize_text(text)
        # return any(pattern in text for pattern in self.DISCOUNT_PATTERNS) and not any(tel_keyword in text for tel_keyword in self.TEL_KEYWORDS)
        return any(pattern in text for pattern in self.DISCOUNT_PATTERNS) 
    
    def is_non_item_line(self, text):
        """sumary_line
        description: ตรวจสอบว่าบรรทัดนั้นเป็นบรรทัดที่ไม่ใช่รายการสินค้าหรือไม่
        parameter text: line text ที่ต้องการตรวจสอบ
        return: True หากเป็นบรรทัดที่ไม่ใช่รายการสินค้า False หากไม่ใช่
        """
        compact = self.normalize_text(text)

        # keyword check
        for keyword in self.NON_ITEM_MASTER["non_item_keywords"]:
            if keyword in compact:
                return True

        # fuzzy check
        for keyword in self.NON_ITEM_MASTER["non_item_keywords"]:
            score = fuzz.partial_ratio(compact, keyword)
            if score >= self.FUZZY_THRESHOLD:
                return True
            
        # regex check
        for pattern in self.NON_ITEM_MASTER["non_item_regex_patterns"]:
            if re.search(pattern, text):
                return True

        return False
    
    
    def detect_summary_key(self, text, threshold=75):
        """sumary_line
        description: ตรวจหาคีย์สรุปจากข้อความ
        parameter text: line text ที่ลบราราคาออกแล้ว
        parameter threshold: ค่า threshold
        return: คีย์สรุปที่พบและคะแนน
        """
        
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
        
    def is_phone_line(self, text):
        """sumary_line
        description: ตรวจสอบว่าบรรทัดนั้นมีหมายเลขโทรศัพท์หรือไม่
        parameter text: line text ที่ต้องการตรวจสอบ
        return: True หากมีหมายเลขโทรศัพท์ False หากไม่มี
        """
        
        return (
            "TEL" in text
            or re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", text)
        )
 
    def normalize_price_text(self, text: str) -> str:
        """sumary_line
        description: ทำความสะอาดข้อความที่เป็นราคาหรือส่วนลด โดยการลบช่องว่างที่ไม่จำเป็นและจัดรูปแบบให้เหมาะสม เพื่อช่วยในการแปลงข้อความเป็นตัวเลขได้แม่นยำขึ้น
        param text: price text เช่น "¥ 4 , 980" หรือ "4 , 980"
        return: cleaned price text เช่น "¥4,980" หรือ "4,980"
        """
        
        # ¥ 4 , 980 -> ¥ 4,980
        text = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', text)

        # 4 , 980 -> 4,980
        text = re.sub(r'\s+', ' ', text)

        return text

    def extract_price(self, text, allow_plain_number=False):
        """sumary_line
        description: ดึงราคาหรือส่วนลดจากข้อความ
        parameter text: line text ที่ต้องการดึงราคา
        parameter allow_plain_number: ตัวเลือกในการอนุญาตให้ดึงตัวเลขธรรมดา
        return: ราคาหรือส่วนลดที่พบ
        """
                
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
        """sumary_line
        description: ทำความสะอาดข้อความที่เป็นราคา
        parameter price_text: price text ที่ต้องการทำความสะอาด
        return: cleaned price text
        """
        
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
        """sumary_line
        description: ลบจำนวนเงินออกจากข้อความ
        parameter text: line text ที่ต้องการลบจำนวนเงิน
        return: text หลังจากลบจำนวนเงินแล้ว
        """
        # ลบ ¥128, ￥128, \ 1.370
        text = re.sub(r"[¥￥\\]\s*[\d,\.]+", "", text)

        # ลบจำนวนเงินที่เหลืออยู่
        text = re.sub(r"\d{1,3}(?:[,.]\d{3})+|\d+", "", text)

        # ลบ -80 หรือ −80 (discount)
        text = re.sub(r"[-−]\s*[\d,\.]+", "", text)

        # ลบ % เช่น 20 %
        text = re.sub(r"\d+\s*%", "", text)

        # ลบช่องว่างซ้ำ
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def parse_receipt_lines(self, lines):
        """sumary_line
        description: แยกบรรทัดของใบเสร็จออกเป็นรายการสินค้าและสรุปยอด
        parameter lines: รายการบรรทัดของใบเสร็จ
        return: object ของใบเสร็จที่แยกแล้ว
        """
        
        receipt_obj = {
            "datetime": None,
            "items": [],
            "summary": {}
        }
        
        for line in lines:
            line = line.strip()

            # ตรวจสอบว่าบรรทัดนั้นมีวันที่หรือไม่
            dt = self.extract_receipt_datetime(line)
            if dt:
                print(f"Extracted datetime: {dt} from line: {line}")
                receipt_obj["datetime"] = dt
                continue
            
            # check non item line
            if self.is_non_item_line(line):
                print(f"Non-item line detected: {line}")
                continue

            # get name by removing price from text
            name = self.remove_amount_from_text(line)

            # หากชื่อว่างเปล่าหลังจากลบจำนวนเงินออก แสดงว่าไม่ใช่รายการสินค้า ให้ข้ามบรรทัดนี้
            if not name:
                continue

            # ตรวจสอบว่าบรรทัดนั้นเป็นบรรทัดสรุปยอดหรือไม่ โดยดูจากการมีคำที่บ่งบอกสรุปยอดและไม่มีคำที่บ่งบอกหมายเลขโทรศัพท์
            key, score = self.detect_summary_key(name)

            # หากเป็นบรรทัดสรุปยอด ให้เก็บไว้ใน summary แทนที่จะเก็บเป็นสินค้า
            if key:
               price = self.extract_price(line, allow_plain_number=True)
               receipt_obj["summary"][key] = price
               print(f"SUMMARY detected: {key}, score={score}, text={name}")
               continue
            else:
                print (f"Not summary line: {name}, score={score}")

            # get price
            price = self.extract_price(line)

            if price is None:
                continue


            if self.is_discount_line(name):
            # หากเป็นบรรทัดส่วนลด ให้หักส่วนลดจากสินค้าก่อนหน้า ถ้าไม่มีสินค้าก่อนหน้าให้เก็บไว้ใน summary แทน
                if receipt_obj["items"]:
                    discount_amount = abs(price)
                    receipt_obj["items"][-1]["price"] -= discount_amount
                    receipt_obj["items"][-1]["discount"] = receipt_obj["items"][-1].get("discount", 0) + discount_amount
                else:
                    receipt_obj["summary"].setdefault("discounts", []).append(line)
                
            else:
                receipt_obj["items"].append({
                    "name": name,
                    "price": price
                })            
            
        return receipt_obj
