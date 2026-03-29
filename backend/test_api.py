import requests
from PIL import Image
import io

# Create a dummy image
img = Image.new('RGB', (224, 224), color = 'gray')
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)

print("Sending request to localhost:8000/api/analyze...")
try:
    files = {"file": ("dummy.jpg", img_bytes, "image/jpeg")}
    response = requests.post("http://localhost:8000/api/analyze", files=files)
    print("Status:", response.status_code)
    try:
        import json
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print("Failed to connect:", e)
