from google.cloud import vision

class OcrProcessor:
    def __init__(self):
        return
    
    def text_ocr(self, image_path: str):

        client = vision.ImageAnnotatorClient()
        
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(response.error.message)
        
        full_text = response.full_text_annotation.text

        print("===== FULL TEXT =====")
        print(full_text)

        return response

