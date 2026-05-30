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
        description: json ファイルからキーワードをロードする関数
        parameter file_name: ファイル名（例: "summary_keywords.json")
        return: キーワードの辞書オブジェクト
        """
        
        if not file_name:
            return ""
        base_dir = Path(__file__).resolve().parent.parent
        file_path = base_dir / "data" / file_name

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    
    def extract_receipt_datetime(self, text: str):
        """sumary_line
        description: テキストからレシートの日付と時間を抽出する関数
        parameter text: 抽出するテキスト
        return: datetime object または None (日付と時間が見つからない場合)
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
        description: テキストを正規化する関数。スペースを削除し、全角スペースを半角スペースに変換し、バックスラッシュを円マークに変換する。
        parameter text: 正規化するテキスト
        return: 正規化されたテキスト
        """
        
        return (
            text.replace(" ", "")
                .replace("　", "")
                .replace("\\", "¥")
                .replace("￥", "¥")
        )
        
    def is_discount_line(self, text):
        """sumary_line
        description: テキストが割引行かどうかを判定する関数
        parameter text: 判定するテキスト
        return: 割引行の場合は True、それ以外の場合は False
        """
        
        text = self.normalize_text(text)        
        return any(pattern in text for pattern in self.DISCOUNT_PATTERNS) 
    
    def is_non_item_line(self, text):
        """sumary_line
        description: テキストが非商品行かどうかを判定する関数
        parameter text: 判定するテキスト
        return: 非商品行の場合は True、それ以外の場合は False
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
        description: テキストからサマリーキーを抽出する関数
        parameter text: 抽出するテキスト
        parameter threshold: 抽出のスコアの閾値（デフォルトは75）。この値以上のスコアが得られた場合にキーを返す。
        return: 抽出されたキーとスコアのタプル。スコアが閾値未満の場合は (None, score) を返す。
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
        description: テキストが電話番号を含む行かどうかを判定する関数
        parameter text: 判定するテキスト
        return: 電話番号を含む場合は True、それ以外の場合は False
        """
        
        return (
            "TEL" in text
            or re.search(r"\d{2,4}-\d{2,4}-\d{3,4}", text)
        )
 
    def normalize_price_text(self, text: str) -> str:
        """sumary_line
        description: 価格または割引のテキストを正規化する関数。不要なスペースを削除し、適切な形式に整形して、テキストを数値に変換しやすくする。
        param text: 価格テキスト（例: "¥ 4 , 980" または "4 , 980"）
        return: 正規化された価格テキスト（例: "¥4,980" または "4,980"）
        """
        
        # ¥ 4 , 980 -> ¥ 4,980
        text = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', text)

        # 4 , 980 -> 4,980
        text = re.sub(r'\s+', ' ', text)

        return text

    def extract_price(self, text, allow_plain_number=False):
        """sumary_line
        description: 価格または割引を抽出する関数
        parameter text: 抽出するテキスト
        parameter allow_plain_number: 通常の数字を抽出することを許可するかどうかのオプション
        return: 抽出された価格または割引
        """
                
        # 電話番号を含む行は価格行ではないと判断して None を返す
        if self.is_phone_line(text):
            return None
        
        # "¥ 4 , 980" 、 "4 , 980"　→ "¥4,980" 、 "4,980" に正規化してから抽出する
        text = self.normalize_price_text(text)

        # 1. 割引の抽出: -80 または −80
        minus_matches = re.findall(r"[-−]\s*[\d,\.]+", text)
        if minus_matches:
            raw = minus_matches[-1]
            raw = re.sub(r"[-−\s,\.]", "", raw)
            return -int(raw)

        # 2. ¥128, \ 1.370　の「¥」,「\」,「￥」　を含む価格の抽出
        price_matches = re.findall(r"[¥￥\\]\s*\d[\d,\.\s]*", text)
        if price_matches:
            raw = price_matches[-1]
            raw = re.sub(r"[¥￥\\\s,\.]", "", raw)
            if raw.isdigit():
                return int(raw)

        # 2. 4,980 などシンボルがない価格の抽出
        price_matches = re.findall(r"\d{1,3}(?:[,.]\d{3})+|\d+", text)

        if price_matches:
            raw = price_matches[-1]
            raw = re.sub(r"[,\.]", "", raw)

            if raw.isdigit():
                return int(raw)
            
        # 3. フォールバック: 合計 / 6 点 * 1,479 (Google Vision がカンマをピリオドに誤認する対策)
        if allow_plain_number:
            nums = re.findall(r"\d[\d,\.]*", text)
            if nums:
                raw = nums[-1]   # 6 と 1.479 → 1.479
                raw = raw.replace(",", "").replace(".", "")
                return int(raw)

        return None

    def normalize_price(self, price_text):
        """sumary_line
        description: 価格テキストを正規化する関数。価格テキストから数字、カンマ、ドット以外の文字を削除し、適切な形式に整形して、整数に変換する。
        parameter price_text: 価格テキスト（例: "¥ 4 , 980" または "4 , 980"）
        return: 正規化された価格テキスト
        """
        
        # ¥ 4 , 980 -> 4980, 4 , 980 -> 4980
        cleaned = re.sub(r"[^\d,\.]", "", price_text)

        #  「,」 と 「.」 → 「.」を排除（日本の価格表記では小数点は通常使用されないため）
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "")

        # 「.」を排除
        elif "." in cleaned:
            cleaned = cleaned.replace(".", "")

        # 「,」を排除
        cleaned = cleaned.replace(",", "")

        return int(cleaned)

    def remove_amount_from_text(self, text):
        """sumary_line
        description: テキストから価格や割引の金額を削除する関数。
        parameter text: 金額を削除するテキスト
        return: 金額が削除された後のテキスト
        """
        # ¥128, ￥128, \ 1.370　の「￥」,「\」,「¥」　を排除
        text = re.sub(r"[¥￥\\]\s*[\d,\.]+", "", text)

        # 4,980 や 1.479 の「,」、「.」を排除
        text = re.sub(r"\d{1,3}(?:[,.]\d{3})+|\d+", "", text)

        # -80 または −80　の「-」を排除 (割引)
        text = re.sub(r"[-−]\s*[\d,\.]+", "", text)

        # 「%」を排除
        text = re.sub(r"\d+\s*%", "", text)

        # スペースを排除
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def parse_receipt_lines(self, lines):
        """sumary_line
        description: レシートのテキスト行を解析して、日付、商品リスト、サマリーを抽出する関数
        parameter lines: リストの行
        return: object のレシート
        """
        
        receipt_obj = {
            "datetime": None,
            "items": [],
            "summary": {}
        }
        
        for line in lines:
            line = line.strip()

            # 日付であるかどうかを確認して、日付を抽出
            dt = self.extract_receipt_datetime(line)
            if dt:
                print(f"Extracted datetime: {dt} from line: {line}")
                receipt_obj["datetime"] = dt
                continue
            
            # 非商品行であるかどうかを確認して、非商品行をスキップ
            if self.is_non_item_line(line):
                print(f"Non-item line detected: {line}")
                continue

            # テキストから金額を削除して、商品名を抽出
            name = self.remove_amount_from_text(line)

            # nameが空の場合は、商品行ではないと判断してスキップ
            if not name:
                continue

            # サマリーキーを検出して、サマリーに保存
            key, score = self.detect_summary_key(name)

            # サマリー行の場合は、サマリーに金額を保存して、次の行へ
            if key:
               price = self.extract_price(line, allow_plain_number=True)
               receipt_obj["summary"][key] = price
               print(f"SUMMARY detected: {key}, score={score}, text={name}")
               continue
            else:
                print (f"Not summary line: {name}, score={score}")

            # 商品行の場合は、商品名と価格を抽出して、商品リストに保存
            price = self.extract_price(line)

            if price is None:
                continue


            if self.is_discount_line(name):
            # 割引行の場合は、最後の商品に割引を適用する。商品がない場合は、サマリーの割引リストに保存する。
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
