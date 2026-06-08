from fastapi import FastAPI, Request
import os
import json
from datetime import datetime

app = FastAPI()

@app.post("/webhook/orders/create")
async def webhook(request: Request):
    try:
        order = await request.json()
        print(f"✅ Received: {order.get('name')}")
        print(f"   Items: {len(order.get('line_items', []))}")
    except Exception as e:
        print(f"Error: {e}")
        return {"error": "Invalid"}, 400
    
    # For now, just log. No Google Sheets yet.
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

handler = app