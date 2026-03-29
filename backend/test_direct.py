import asyncio
from app.services.gemini_service import analyze_with_gemini
import io
import os
from PIL import Image

# create dummy image
img = Image.new('RGB', (10, 10), color = 'gray')
img_path = 'dummy.jpg'
img.save(img_path)

async def main():
    try:
        print("Testing direct...")
        res = await analyze_with_gemini(img_path, None, "bone")
        print(res)
    except Exception as e:
        print("Error:", e)
        
    os.remove(img_path)

asyncio.run(main())
