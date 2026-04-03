import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

def debug():
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
    
    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    test_fields = {
        "Client Name": "Debug Test",
        "Primary Contact Email": "debug@example.com",
        "Status": "Complete",
        "google_drive_link": "https://google.com",
        "notion_page_link": "https://notion.so"
    }
    
    print(f"Testing fields one by one in table '{table_name}'...")
    
    # First, test the primary field alone
    try:
        table.create({"Client Name": "Primary Field Test"})
        print("[OK] 'Client Name' is valid.")
    except Exception as e:
        print(f"[FAIL] 'Client Name' failed: {e}")
        return

    # Now test the others
    for key, value in test_fields.items():
        if key == "Client Name": continue
        try:
            # We must include the primary field in every create usually, or at least a valid record
            table.create({"Client Name": f"Test {key}", key: value})
            print(f"[OK] '{key}' is valid.")
        except Exception as e:
            print(f"[FAIL] '{key}' failed: {e}")

if __name__ == "__main__":
    debug()
