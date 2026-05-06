from pathlib import Path
from PIL import Image, ImageOps
import cv2
import numpy as np

class ReceiptImagePreprocessor:
    def __init__(self, max_width=1600):
        self.max_width = max_width

    def preprocess(self,  image_raw_path: str, processed_path: str):
        input_path = Path(image_raw_path)
        image_name = input_path.name
        rotated_image_path = Path(processed_path) / f"rotated_{image_name}"
        bold_image_path = Path(processed_path) / f"bold_{image_name}"

        self.rotate_image(input_path, rotated_image_path)
        
        self.sharpen_threshold(rotated_image_path, bold_image_path)

        return bold_image_path


    def rotate_image(self, input_path, output_path):
        input_path = Path(input_path)
        output_path = Path(output_path)

        img = Image.open(input_path)

        # auto rotate ตาม EXIF
        img = ImageOps.exif_transpose(img)

        # RGB normalize
        img = img.convert("RGB")

        # resize not over [max_width] by keeping aspect ratio
        img = self.resize_keep_ratio(img)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=95)

        return output_path

    # ปรับขนาดรูปภาพโดยรักษาอัตราส่วน (aspect ratio) และไม่ให้ความกว้างเกิน max_width
    def resize_keep_ratio(self, img):
        width, height = img.size

        if width <= self.max_width:
            return img

        ratio = self.max_width / width
        new_height = int(height * ratio)

        return img.resize((self.max_width, new_height))
    
    # sharpen in kernel form (may cause noise if receipt is already clear)
    def sharpen_kernel(self, input_path, output_path):
        img = cv2.imread(input_path)

        # grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # contrast เบา ๆ
        gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=10)

        # sharpen
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        sharp = cv2.filter2D(gray, -1, kernel)

        cv2.imwrite(output_path, sharp)
    
    # sharpen by thresholding (ทำให้พื้นขาวสะอาด ตัวหนังสือดำเข้ม) → เหมาะกับ OCR ที่เน้นอ่านตัวหนังสือเป็นหลัก
    def sharpen_threshold(self, input_path, output_path):

        img = cv2.imread(input_path, 0) # read as Grayscale
        
        # Adjust contrast more intensively (make text darker on light background)
        #_, thresh = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY_INV)
        thresh = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
        
        # Expand text size (Dilation) to connect broken lines
        kernel = np.ones((1,1), np.uint8)
        img_dilation = cv2.dilate(thresh, kernel, iterations=1)
        
        # กลับสีกลับมาเป็นตัวหนังสือดำพื้นขาว Change the color back to black text on a white background.
        final_img = cv2.bitwise_not(img_dilation)
        cv2.imwrite(output_path, final_img)