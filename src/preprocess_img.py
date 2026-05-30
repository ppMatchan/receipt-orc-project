from pathlib import Path
from PIL import Image, ImageOps
import cv2
import numpy as np

class ReceiptImagePreprocessor:
    def __init__(self, max_width=1600):
        self.max_width = max_width

    def preprocess(self,  image_raw_path: str, processed_path: str):
        """ 画像をOCRに適した状態に前処理する
        1. 画像の自動回転
        2. 閾値でシャープ化して文字をくっきりさせる  """
        input_path = Path(image_raw_path)
        image_name = input_path.name
        rotated_image_path = Path(processed_path) / f"rotated_{image_name}"
        bold_image_path = Path(processed_path) / f"bold_{image_name}"

        self.rotate_image(input_path, rotated_image_path)
        
        self.sharpen_threshold(rotated_image_path, bold_image_path)

        return bold_image_path


    def rotate_image(self, input_path, output_path):
        """ 画像を回転 """
        input_path = Path(input_path)
        output_path = Path(output_path)

        img = Image.open(input_path)

        # EXIFで画像を回転
        img = ImageOps.exif_transpose(img)

        # RGB 正規化
        img = img.convert("RGB")

        # サイズを調整（幅が max_width を超える場合のみ）
        img = self.resize_keep_ratio(img)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=95)

        return output_path

    
    def resize_keep_ratio(self, img):
        """画像をリサイズして幅を max_width に収める（アスペクト比を維持）"""
        
        width, height = img.size

        if width <= self.max_width:
            return img

        ratio = self.max_width / width
        new_height = int(height * ratio)

        return img.resize((self.max_width, new_height))
    
    
    def sharpen_kernel(self, input_path, output_path):
        """ カーネル形式で画像をシャープ化する """
        img = cv2.imread(input_path)

        # グレースケール化してコントラストを上げる
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # コントラストを上げる
        gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=10)

        # シャープ化のカーネルを定義
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        sharp = cv2.filter2D(gray, -1, kernel)

        cv2.imwrite(output_path, sharp)
    

    def sharpen_threshold(self, input_path, output_path):
        """" 閾値で画像をシャープ化する """

        img = cv2.imread(input_path, 0) # グレースケールで読み込む
        
        # 閾値処理で文字をくっきりさせる
        #_, thresh = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY_INV)
        thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
        
        # 膨張処理で文字を太くする
        kernel = np.ones((1,1), np.uint8)
        img_dilation = cv2.dilate(thresh, kernel, iterations=1)
        
        # 反転して保存
        final_img = cv2.bitwise_not(img_dilation)
        cv2.imwrite(output_path, final_img)