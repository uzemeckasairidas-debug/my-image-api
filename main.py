import os
import io
import requests
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont

app = FastAPI()
MY_SECRET_KEY = "my-super-secret-123"

class ImageRequest(BaseModel):
    url: str
    caption: str

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Wrong Password!")

@app.post("/process-image")
async def process(request: ImageRequest, x_api_key: str = Depends(verify_api_key)):
    # 1. Get the image
    response = requests.get(request.url)
    arr = np.frombuffer(response.content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    
    # 2. Crop to Square
    h, w = img.shape[:2]
    side = min(h, w)
    img = img[(h-side)//2 : (h+side)//2, (w-side)//2 : (w+side)//2]
    
    # 3. Add Caption with Background Bar for visibility
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # Limit to 3 words and make uppercase
    short_text = " ".join(request.caption.split()[:3]).upper()
    
    # Draw a black bar at the bottom for the text
    # [left, top, right, bottom]
    draw.rectangle([0, side-50, side, side], fill="black")
    
    # Draw the text in white
    # Positioned slightly up from the very bottom
    draw.text((20, side-35), short_text, fill="white")
    
    # 4. Send back
    buf = io.BytesIO()
    img_pil.save(buf, format='JPEG')
    return Response(content=buf.getvalue(), media_type="image/jpeg")
