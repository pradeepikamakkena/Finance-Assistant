import pytesseract
from PIL import Image

def extract_text_from_image(image_path):
    """
    Extracts text from an image using Tesseract OCR.
    It is configured to recognize both English and Japanese characters
    using the advanced LSTM OCR engine and a specific page segmentation mode.
    """
    try:
        image = Image.open(image_path)
       
        custom_config = r'-l eng+jpn --oem 1 --psm 6'
        
        text = pytesseract.image_to_string(image, config=custom_config)
        return text
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""