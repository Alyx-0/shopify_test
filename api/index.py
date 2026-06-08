from fastapi import FastAPI, Request, BackgroundTasks
import hmac
import hashlib
import json
import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

# Configuration (from environment variables)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Google Sheets configuration
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "TestEZImport")

def get_google_sheets_client():
    """Authenticate and return Google Sheets client"""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    else:
        raise Exception("GOOGLE_CREDENTIALS environment variable not set")
    return build('sheets', 'v4', credentials=creds)

def verify_webhook(payload: bytes, signature: str) -> bool:
    """Verify webhook came from Shopify"""
    if not signature or not WEBHOOK_SECRET:
        return True  # Skip verification if no secret (testing)
    
    digest = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(digest, signature)

def append_to_sheets(order: dict):
    """Append order data to Google Sheets"""
    try:
        sheets_client = get_google_sheets_client()
        
        rows = []
        line_items = order.get('line_items', [])
        
        for item in line_items:
            row = [
                order.get('name', ''),
                order.get('customer', {}).get('email', ''),
                order.get('financial_status', ''),
                order.get('processed_at', ''),
                order.get('fulfillment_status', ''),
                item.get('title', ''),
                item.get('quantity', 0),
                item.get('price', 0),
                float(item.get('quantity', 0)) * float(item.get('price', 0)),
                order.get('total_price', 0),
                datetime.now().isoformat()
            ]
            rows.append(row)
        
        if rows:
            body = {'values': rows}
            sheets_client.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:K",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            print(f"✅ Appended {len(rows)} rows for order {order.get('name')}")
            
    except Exception as e:
        print(f"❌ Error appending to sheets: {e}")

def process_order(order: dict):
    """Process the order data"""
    print(f"\n📦 Processing order: {order.get('name', 'Unknown')}")
    print(f"   Customer: {order.get('customer', {}).get('email', 'Unknown')}")
    print(f"   Total: ${order.get('total_price', '0')}")
    print(f"   Items: {len(order.get('line_items', []))}")
    
    append_to_sheets(order)
    
    print(f"✅ Order {order.get('name')} processed successfully!")

@app.post("/webhook/orders/create")
async def shopify_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_shopify_hmac_sha256: str = None
):
    """Receive Shopify order webhook"""
    
    body = await request.body()
    
    # Verify webhook signature
    if not verify_webhook(body, x_shopify_hmac_sha256):
        return {"error": "Invalid webhook signature"}, 401
    
    try:
        order = await request.json()
        print(f"✅ Received order: {order.get('name', 'Unknown')}")
    except:
        return {"error": "Invalid JSON"}, 400
    
    # Process order in background
    background_tasks.add_task(process_order, order)
    
    return {"status": "ok", "message": "Webhook received"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Shopify to Google Sheets"}

# Vercel needs this handler
handler = app