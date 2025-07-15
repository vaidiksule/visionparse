import os
import base64
import requests
from decouple import config
import mimetypes
import re

GEMINI_API_KEY = config("GEMINI_API_KEY")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def extract_data_from_file(file_path, prompt=None):
    print(f"[Gemini] Fetching file: {file_path}")
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    with open(file_path, "rb") as f:
        file_content = base64.b64encode(f.read()).decode("utf-8")
    print(f"[Gemini] File fetched and encoded. Mime type: {mime_type}")

    if prompt is None:
        prompt = "Extract all invoice fields (invoice number, total, date, etc.) in JSON."

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": file_content
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    print(f"[Gemini] Sending request to Gemini API...")
    response = requests.post(
        f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}",
        json=payload
    )
    print(f"[Gemini] Response status: {response.status_code}")
    print(f"[Gemini] Raw response: {response.text}")
    if response.status_code == 200:
        try:
            result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            print(f"[Gemini] Extracted JSON text: {result}")
            # Remove triple backticks and optional 'json' label
            cleaned = re.sub(r'^```json\s*|^```\s*|```$', '', result.strip(), flags=re.MULTILINE)
            cleaned = cleaned.strip()
            print(f"[Gemini] Cleaned JSON text: {cleaned}")
            return cleaned
        except Exception as e:
            print(f"[Gemini] Error parsing response: {e}")
            return "{}"  # Fallback if structure is unexpected
    else:
        print(f"[Gemini] Error from Gemini API: {response.text}")
        return "{}"  # Fallback 