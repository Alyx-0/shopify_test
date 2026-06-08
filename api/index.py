from fastapi import FastAPI, Request
import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Configuration
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "TestEZImport")

print(f"🔍 DEBUG: SPREADSHEET_ID = {SPREADSHEET_ID[:10] if SPREADSHEET_ID else 'NOT SET'}...")
print(f"🔍 DEBUG: SHEET_NAME = {SHEET_NAME}")
print(f"🔍 DEBUG: GOOGLE_CREDENTIALS = {'SET' if os.environ.get('GOOGLE_CREDENTIALS') else 'NOT SET'}")

executor = ThreadPoolExecutor(max_workers=1)

def get_google_sheets_client():
    """Authenticate and return Google Sheets client"""
    print("🔍 DEBUG: get_google_sheets_client() STARTED")
    
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    print(f"🔍 DEBUG: creds_json exists: {bool(creds_json)}")
    
    if not creds_json:
        raise Exception("GOOGLE_CREDENTIALS environment variable not set")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        print("🔍 DEBUG: Parsing JSON...")
        creds_dict = json.loads(creds_json)
        print(f"🔍 DEBUG: JSON parsed, client_email = {creds_dict.get('client_email', 'NOT FOUND')}")
        
        print("🔍 DEBUG: Creating credentials...")
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        print("🔍 DEBUG: Building sheets client...")
        client = build('sheets', 'v4', credentials=creds)
        print("✅ DEBUG: Sheets client created successfully")
        return client
    except Exception as e:
        print(f"❌ DEBUG: Error in get_google_sheets_client: {e}")
        raise

def append_to_sheets(order: dict):
    """Append order data to Google Sheets"""
    print(f"🔍 DEBUG: append_to_sheets() STARTED for order {order.get('name')}")
    
    try:
        print("🔍 DEBUG: Getting sheets client...")
        sheets_client = get_google_sheets_client()
        
        print("🔍 DEBUG: Building rows...")
        rows = []
        line_items = order.get('line_items', [])
        print(f"🔍 DEBUG: Found {len(line_items)} line items")
        
        for idx, item in enumerate(line_items):
            print(f"🔍 DEBUG: Processing item {idx}: {item.get('title')}")
            row = [
                order.get('name', ''),
                order.get('customer', {}).get('email', ''),
                item.get('title', ''),
                str(item.get('quantity', 0)),
                str(item.get('price', 0)),
                datetime.now().isoformat()
            ]
            rows.append(row)
        
        print(f"🔍 DEBUG: {len(rows)} rows built")
        
        if rows:
            print(f"🔍 DEBUG: Calling Google Sheets API...")
            body = {'values': rows}
            result = sheets_client.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:F",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            print(f"✅ DEBUG: SUCCESS! Appended {len(rows)} rows")
            print(f"✅ DEBUG: Response: {result}")
        else:
            print("⚠️ DEBUG: No rows to append")
            
    except Exception as e:
        print(f"❌ DEBUG: Error in append_to_sheets: {e}")
        import traceback
        traceback.print_exc()

def process_in_background(order: dict):
    """Background processing"""
    print(f"🔍 DEBUG: process_in_background() STARTED for {order.get('name')}")
    try:
        append_to_sheets(order)
        print(f"✅ DEBUG: process_in_background() COMPLETED for {order.get('name')}")
    except Exception as e:
        print(f"❌ DEBUG: process_in_background() FAILED: {e}")

@app.post("/webhook/orders/create")
async def webhook(request: Request):
    print("🔍 DEBUG: webhook() CALLED")
    
    try:
        body = await request.body()
        print(f"🔍 DEBUG: Body received, length: {len(body)}")
        
        order = await request.json()
        print(f"✅ DEBUG: Received order: {order.get('name')}")
        print(f"🔍 DEBUG: Order keys: {list(order.keys())}")
        print(f"🔍 DEBUG: line_items count: {len(order.get('line_items', []))}")
        
    except Exception as e:
        print(f"❌ DEBUG: Error parsing order: {e}")
        return {"error": "Invalid JSON"}, 400
    
    print("🔍 DEBUG: Submitting to background thread...")
    executor.submit(process_in_background, order)
    print("🔍 DEBUG: Background task submitted")
    
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Required for Vercel
handler = app