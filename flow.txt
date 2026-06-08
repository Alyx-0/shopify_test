# from fastapi import FastAPI, Request, BackgroundTasks
# import hmac
# import hashlib
# import json
# import os
# from datetime import datetime
# from google.oauth2 import service_account
# from googleapiclient.discovery import build

# app = FastAPI()

# # Configuration
# WEBHOOK_SECRET = "aa5fb3f99bf578123e53f485e935249ff8fcf0cc5c491bed69f873495b8b05a4"

# # Google Sheets configuration
# SPREADSHEET_ID = "1Fq-8E5Mo71UR-HdUOAJrLXd959jVRyVj8Q2oOr7lfR8"
# SHEET_NAME = "TestEZImport"

# # Local file (only used for development)
# SERVICE_ACCOUNT_FILE = "probable-sprite-498507-i8-eff401ef074e.json"

# def get_google_sheets_client():
#     """Authenticate and return Google Sheets client"""
#     # Try environment variable first (for Render)
#     creds_json = os.environ.get("GOOGLE_CREDENTIALS")
#     if creds_json:
#         creds_dict = json.loads(creds_json)
#         creds = service_account.Credentials.from_service_account_info(
#             creds_dict,
#             scopes=['https://www.googleapis.com/auth/spreadsheets']
#         )
#     else:
#         # Fallback to file for local development
#         creds = service_account.Credentials.from_service_account_file(
#             SERVICE_ACCOUNT_FILE,
#             scopes=['https://www.googleapis.com/auth/spreadsheets']
#         )
#     return build('sheets', 'v4', credentials=creds)

# def verify_webhook(payload: bytes, signature: str) -> bool:
#     """Verify webhook came from Shopify"""
#     if not signature:
#         return False
    
#     digest = hmac.new(
#         WEBHOOK_SECRET.encode('utf-8'),
#         payload,
#         hashlib.sha256
#     ).hexdigest()
    
#     return hmac.compare_digest(digest, signature)

# def append_to_sheets(order: dict):
#     """Append order data to Google Sheets"""
#     try:
#         sheets_client = get_google_sheets_client()
        
#         rows = []
#         line_items = order.get('line_items', [])
        
#         for item in line_items:
#             row = [
#                 order.get('name', ''),
#                 order.get('customer', {}).get('email', ''),
#                 order.get('financial_status', ''),
#                 order.get('processed_at', ''),
#                 order.get('fulfillment_status', ''),
#                 item.get('title', ''),
#                 item.get('quantity', 0),
#                 item.get('price', 0),
#                 float(item.get('quantity', 0)) * float(item.get('price', 0)),
#                 order.get('total_price', 0),
#                 datetime.now().isoformat()
#             ]
#             rows.append(row)
        
#         if rows:
#             body = {'values': rows}
#             sheets_client.spreadsheets().values().append(
#                 spreadsheetId=SPREADSHEET_ID,
#                 range=f"{SHEET_NAME}!A:K",
#                 valueInputOption='USER_ENTERED',
#                 body=body
#             ).execute()
#             print(f"✅ Appended {len(rows)} rows for order {order.get('name')}")
#         else:
#             print(f"⚠️ No rows to append for order {order.get('name')}")
            
#     except Exception as e:
#         print(f"❌ Error appending to sheets: {e}")
#         import traceback
#         traceback.print_exc()

# def process_order(order: dict):
#     """Process the order data"""
#     print(f"\n📦 Processing order: {order.get('name', 'Unknown')}")
#     print(f"   Customer: {order.get('customer', {}).get('email', 'Unknown')}")
#     print(f"   Total: ${order.get('total_price', '0')}")
#     print(f"   Items: {len(order.get('line_items', []))}")
    
#     append_to_sheets(order)
    
#     print(f"✅ Order {order.get('name')} processed successfully!")

# @app.post("/webhook/orders/create")
# async def shopify_webhook(
#     request: Request,
#     background_tasks: BackgroundTasks,
#     x_shopify_hmac_sha256: str = None
# ):
#     """Receive Shopify order webhook"""
    
#     body = await request.body()
    
#     # Temporarily disabled for testing
#     # if not verify_webhook(body, x_shopify_hmac_sha256):
#     #     return {"error": "Invalid webhook signature"}, 401
    
#     try:
#         order = await request.json()
#         print(f"✅ Received order: {order.get('name', 'Unknown')}")
#     except:
#         return {"error": "Invalid JSON"}, 400
    
#     background_tasks.add_task(process_order, order)
    
#     return {"status": "ok", "message": "Webhook received"}

# @app.get("/health")
# async def health():
#     """Health check endpoint"""
#     return {"status": "healthy", "service": "Shopify to Google Sheets"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)