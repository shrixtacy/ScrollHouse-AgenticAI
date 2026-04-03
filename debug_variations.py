import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

def debug_variations():
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
    
    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    variations = [
        "google_drive_link", "Google Drive Link", "Google drive link",
        "notion_page_link", "Notion Hub Link", "Notion page link", "Notion Hub"
    ]
    
    print(f"Testing variations in table '{table_name}'...")
    
    for var in variations:
        try:
            table.create({"Client Name": f"Var Test {var}", var: "https://test.com"})
            print(f"[SUCCESS] '{var}' is the correct name!")
        except Exception as e:
            # Check if it's an 'Unknown field name' error
            if "Unknown field name" in str(e):
                continue
            else:
                print(f"[OTHER ERROR] '{var}': {e}")

if __name__ == "__main__":
    debug_variations()
