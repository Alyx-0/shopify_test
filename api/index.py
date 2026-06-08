from fastapi import FastAPI, Request
import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI()

# Configuration
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
SHEET_NAME = os.environ.get("SHEET_NAME", "TestEZImport")

def get_google_sheets_client():
    """Authenticate and return Google Sheets client"""
    print("🔍 Getting Google credentials...")
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if not creds_json:
        error_msg = "GOOGLE_CREDENTIALS environment variable not set!"
        print(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    print("🔍 Parsing credentials JSON...")
    creds_dict = json.loads(creds_json)
    print(f"✅ Using service account: {creds_dict.get('client_email')}")
    
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    print("🔍 Building Google Sheets client...")
    return build('sheets', 'v4', credentials=creds)

@app.post("/webhook/orders/create")
async def webhook(request: Request):
    print("=" * 50)
    print("📦 WEBHOOK RECEIVED")
    
    # Parse order
    try:
        order = await request.json()
        print(f"✅ Order: {order.get('name')}")
        print(f"   Customer: {order.get('customer', {}).get('email', 'N/A')}")
        print(f"   Items: {len(order.get('line_items', []))}")
    except Exception as e:
        print(f"❌ Error parsing: {e}")
        return {"error": "Invalid JSON"}, 400
    
    # Process Google Sheets DIRECTLY (not in background)
    try:
        print("🔍 Getting sheets client...")
        sheets_client = get_google_sheets_client()
        print("✅ Sheets client ready")
        
        rows = []
        for item in order.get('line_items', []):
            row = [
                order.get('name', ''),
                order.get('customer', {}).get('email', ''),
                item.get('title', ''),
                str(item.get('quantity', 0)),
                str(item.get('price', 0)),
                datetime.now().isoformat()
            ]
            rows.append(row)
            print(f"   Added row for: {item.get('title')}")
        
        if rows:
            print(f"🔍 Appending {len(rows)} rows to Google Sheets...")
            print(f"   Sheet: {SHEET_NAME}")
            print(f"   Spreadsheet ID: {SPREADSHEET_ID[:10]}...")
            
            body = {'values': rows}
            result = sheets_client.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A:F",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            print(f"✅ SUCCESS! Appended {len(rows)} rows")
            print(f"   Updated range: {result.get('updates', {}).get('updatedRange')}")
        else:
            print("⚠️ No line items found in order")
            
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500
    
    print("=" * 50)
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Required for Vercel
handler = app