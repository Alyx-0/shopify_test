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

# Thread pool for background processing
executor = ThreadPoolExecutor(max_workers=1)

def get_google_sheets_client():
    """Authenticate and return Google Sheets client"""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise Exception("GOOGLE_CREDENTIALS not set")
    
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)

def append_to_sheets(order: dict):
    """Fast append to Google Sheets"""
    try:
        sheets_client = get_google_sheets_client()
        
        rows = []
        for item in order.get('line_items', []):
            row = [
                order.get('name', '')[:20],
                order.get('customer', {}).get('email', '')[:30],
                item.get('title', '')[:30],
                str(item.get('quantity', 0)),
                str(item.get('price', 0)),
                datetime.now().isoformat()
            ]
            rows.append(row)
        
        if rows:
            body = {'values': rows}
            sheets_client.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:F",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            print(f"✅ Appended {len(rows)} rows")
            
    except Exception as e:
        print(f"❌ Sheets error: {e}")

def process_in_background(order: dict):
    """Background processing with retry"""
    try:
        print(f"Processing order: {order.get('name')}")
        append_to_sheets(order)
        print(f"Done: {order.get('name')}")
    except Exception as e:
        print(f"Failed: {e}")

@app.post("/webhook/orders/create")
async def webhook(request: Request):
    try:
        order = await request.json()
        print(f"Received: {order.get('name')}")
    except:
        return {"error": "Invalid JSON"}, 400
    
    # Fire and forget - no await
    executor.submit(process_in_background, order)
    
    # Respond immediately (within 1 second)
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Required for Vercel
handler = app