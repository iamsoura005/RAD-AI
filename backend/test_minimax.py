import requests
import json
import base64

# encode dummy image
import io
from PIL import Image
img = Image.new('RGB', (10, 10), color = 'gray')
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
b64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {"Authorization": "Bearer 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", "Content-Type": "application/json"}
payload = {
    "model": "minimax/minimax-m2.5:free",
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
    ]}]
}
response = requests.post(url, headers=headers, json=payload)
print(response.status_code, response.text)
