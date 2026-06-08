from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhook/orders/create")
async def webhook(request: Request):
    try:
        order = await request.json()
        print(f"✅ Received order: {order.get('name')}")
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

handler = app