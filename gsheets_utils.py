import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os

# Define the scope and credentials
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
CREDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                         'credentials', 'isro-kiosk-credentials.json')

def get_google_sheets_client():
    """Get authenticated Google Sheets client"""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Error authenticating: {str(e)}")
        return None

def append_to_sheet(data_row):
    """Append a row of data to the Google Sheet"""
    try:
        client = get_google_sheets_client()
        # Open the spreadsheet by its title
        sheet = client.open('ISRO_Kiosk_Feedback').sheet1
        sheet.append_row(data_row)
        return True
    except Exception as e:
        print(f"Error appending to sheet: {str(e)}")
        return False

def get_filtered_data(filters=None):
    """Get data from sheet with optional filters
    filters can include:
    - date_from: datetime
    - date_to: datetime
    - college: str
    - role: str
    """
    try:
        client = get_google_sheets_client()
        sheet = client.open('ISRO_Kiosk_Feedback').sheet1
        
        # Get all data including headers
        all_data = sheet.get_all_records()
        
        if not filters:
            return all_data
            
        filtered_data = []
        for row in all_data:
            include_row = True
            
            # Apply date filter
            if 'date_from' in filters or 'date_to' in filters:
                row_date = datetime.datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
                
                if 'date_from' in filters and row_date < filters['date_from']:
                    include_row = False
                if 'date_to' in filters and row_date > filters['date_to']:
                    include_row = False
            
            # Apply college filter
            if 'college' in filters and filters['college'].lower() not in row['College'].lower():
                include_row = False
                
            # Apply role filter
            if 'role' in filters and filters['role'].lower() != row['Role'].lower():
                include_row = False
            
            if include_row:
                filtered_data.append(row)
                
        return filtered_data
        
    except Exception as e:
        print(f"Error getting data from sheet: {str(e)}")
        return []
