import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

try:
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
except KeyError:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit()

model = genai.GenerativeModel('gemini-1.5-flash')

def parse_receipt_with_gemini(ocr_text: str) -> dict:
    """
    Sends the OCR-extracted receipt text to Gemini and returns a structured dictionary.
    """
    prompt = f"""
You are an expert AI assistant that extracts structured data from OCR text of a receipt. The text may be in English or Japanese.

Your instructions are:
1.  Analyze the text to understand the content, regardless of the language.
2.  Based on the seller's name and items, classify the receipt into one of these exact English categories: "Groceries", "Dining Out", "Shopping", "Fuel", "Entertainment", "Travel", "Utilities", "Other".
3.  If you see multiple tax amounts, add them all together to get the single total_tax amount.

Extract the following fields and return the result in a valid JSON format with English keys.
- seller_name (in its original language)
- category (must be one of the English words from the list above)
- receipt_date (in "YYYY-MM-DDTHH:MM:SS" format)
- items (a list of objects, each with item_name, quantity, rate, and subtotal)
- total_amount
- tax_amount

IMPORTANT: Your entire output must be only the raw JSON object. Do not include any other text or explanations.

Receipt Text:
\"\"\"
{ocr_text}
\"\"\"
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start != -1 and json_end != 0:
            json_string = response_text[json_start:json_end]
            return json.loads(json_string)
        else:
            print("Error: Could not find a valid JSON object in the AI response.")
            return {}
            
    except Exception as e:
        print(f"Error parsing receipt with Gemini: {e}")
        print(f"Full AI Response was: {response_text}")
        return {}