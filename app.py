import os
import json
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, render_template

app = Flask(__name__)

# CONFIGURATION
TARGET_AMOUNT = 1500
SHEET_NAME = "iftar" # Updated based on user's latest info
SERVICE_ACCOUNT_FILE = 'service_account.json'

def get_donation_data():
    """Fetches data from Google Sheets or returns mock data if keys are missing."""
    creds_json = os.environ.get('GOOGLE_CREDS_JSON')
    
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        source = "None"
        
        if creds_json:
            source = "Environment Variable (GOOGLE_CREDS_JSON)"
            info = json.loads(creds_json)
            # Triple check newline handling
            if 'private_key' in info:
                info['private_key'] = info['private_key'].strip().replace('\\n', '\n')
            creds = Credentials.from_service_account_info(info, scopes=scopes)
        elif os.path.exists(SERVICE_ACCOUNT_FILE):
            source = f"Local File ({SERVICE_ACCOUNT_FILE})"
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                info = json.load(f)
                if 'private_key' in info:
                    info['private_key'] = info['private_key'].strip().replace('\\n', '\n')
                creds = Credentials.from_service_account_info(info, scopes=scopes)
        else:
            return {
                "total": 450,
                "top_3": [200, 150, 100],
                "error": "No credentials found (check Render Environment Variables)."
            }
            
        client = gspread.authorize(creds)
        
        # Log source in case of later errors
        print(f"Using credentials from: {source}")
        
        sheet = client.open(SHEET_NAME).sheet1
        # Assumes donations are in the first column (Column A)
        # You can adjust this based on your sheet structure
        values = sheet.col_values(1)[1:] # Skip header
        
        donations = []
        for val in values:
            try:
                # Clean value (remove currency symbols, commas)
                clean_val = float(val.replace('JOD', '').replace(',', '').strip())
                donations.append(clean_val)
            except ValueError:
                continue
                
        total = sum(donations)
        top_3 = sorted(donations, reverse=True)[:3]
        
        return {
            "total": total,
            "top_3": top_3,
            "error": None,
            "source": source
        }
    except Exception as e:
        return {
            "total": 0,
            "top_3": [],
            "error": str(e),
            "source": source
        }

@app.route('/')
def index():
    data = get_donation_data()
    progress_percent = min((data['total'] / TARGET_AMOUNT) * 100, 100)
    
    return render_template(
        'index.html', 
        total=data['total'], 
        target=TARGET_AMOUNT, 
        progress=progress_percent,
        top_3=data['top_3'],
        error=data['error'],
        source=data.get('source', 'Unknown')
    )

if __name__ == '__main__':
    app.run(debug=True)
