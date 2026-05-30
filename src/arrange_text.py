
# テキストを行ごとに配置するためのクラス
class ArrangeTextPosition:
    def __init__(self):
        return


    def get_text_by_lines(self,response):
        """ Google Vision APIのresponseからテキストを行ごとに配置して取得するメソッド"""

        words = self.sort_words_from_response(response)

        if not words:
            return []

        lines = []

        for word in words:
            added = False

            for line in lines:
                # 行の平均高さとy座標を使って、単語が行に属するかどうかを判断
                tolerance = max(12, line["avg_h"] * 0.6)

                if abs(word["y"] - line["avg_y"]) <= tolerance:
                    line["words"].append(word)

                    # 行の平均y座標と平均高さを更新
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

        # 垂直方向に並べ替え
        lines.sort(key=lambda l: l["avg_y"])

        result = []
        for line in lines:
            # 行内の単語をx座標で並べ替える
            line["words"].sort(key=lambda w: w["x"])
            text = " ".join(w["text"] for w in line["words"])
            result.append(text)

        return result


    def sort_words_from_response(self, words):
        """Google Vision APIのresponseから単語をy座標で並び替える"""
        
        sorted_words = []

        # Google Vision APIのresponseから単語とその位置情報を抽出して、リストに追加
        for page in words.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        text = "".join([s.text for s in word.symbols])

                        # 単語のバウンディングボックスからx座標とy座標を取得
                        xs = [v.x for v in word.bounding_box.vertices]
                        ys = [v.y for v in word.bounding_box.vertices]

                        #  単語の左端のx座標、中央のy座標、高さを計算
                        x_min = min(xs)
                        y_center = sum(ys) / 4
                        height = max(ys) - min(ys)

                        # 単語と位置情報をリストに追加
                        sorted_words.append({
                            "text": text,
                            "x": x_min,
                            "y": y_center,
                            "h": height
                        })

        # 単語をy座標で並べ替える（同じ行の単語が近くに来るようにするため）
        sorted_words.sort(key=lambda w: (w["y"], w["x"]))

        return sorted_words