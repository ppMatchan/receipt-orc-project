
class ArrangeTextPosition:
    def __init__(self):
        return

    # arrange text by line based on y coordinate and height of words
    def get_text_by_lines(self,response):
        
        words = self.sort_words_from_response(response)

        if not words:
            return []

        lines = []

        for word in words:
            added = False

            for line in lines:
                # ใช้ tolerance ตามความสูงตัวอักษร
                tolerance = max(12, line["avg_h"] * 0.6)

                if abs(word["y"] - line["avg_y"]) <= tolerance:
                    line["words"].append(word)

                    # update ค่าเฉลี่ยของ line
                    n = len(line["words"])
                    line["avg_y"] = sum(w["y"] for w in line["words"]) / n
                    line["avg_h"] = sum(w["h"] for w in line["words"]) / n

                    added = True
                    break

            if not added:
                lines.append({
                    "avg_y": word["y"],
                    "avg_h": word["h"],
                    "words": [word]
                })

        # เรียงบรรทัดจากบนลงล่าง
        lines.sort(key=lambda l: l["avg_y"])

        result = []
        for line in lines:
            # เรียงคำในบรรทัดจากซ้ายไปขวา
            line["words"].sort(key=lambda w: w["x"])
            text = " ".join(w["text"] for w in line["words"])
            result.append(text)

        return result
    
    # จัดเรียงคำจาก response ของ Google Vision API โดยใช้พิกัดของ bounding box
    def sort_words_from_response(self, words):
        sorted_words = []

        # ดึงคำและพิกัดจาก responseของ Google Vision API
        for page in words.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        text = "".join([s.text for s in word.symbols])

                        # ดึงพิกัดของคำจาก bounding box    
                        xs = [v.x for v in word.bounding_box.vertices]
                        ys = [v.y for v in word.bounding_box.vertices]

                        # ใช้พิกัด x น้อยสุดเป็นตำแหน่งเริ่มต้นของคำ และคำนวณ y center กับ height เพื่อใช้ในการจัดกลุ่มคำเป็นบรรทัด
                        x_min = min(xs)
                        y_center = sum(ys) / 4
                        height = max(ys) - min(ys)

                        # เพิ่มคำและพิกัดลงในรายการ sorted_words
                        sorted_words.append({
                            "text": text,
                            "x": x_min,
                            "y": y_center,
                            "h": height
                        })

        # เรียงคำจากบนลงล่าง และจากซ้ายไปขวา
        sorted_words.sort(key=lambda w: (w["y"], w["x"]))

        return sorted_words