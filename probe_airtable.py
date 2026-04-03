import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

def probe():
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
    
    if not api_key or not base_id:
        print("Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID in .env")
        return

    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    try:
        # Try to get one record to see the field names
        records = table.all(max_records=1)
        if records:
            print(f"Found a record! Actual field names in Airtable '{table_name}':")
            for field in records[0]['fields'].keys():
                print(f" - {field}")
        else:
            print(f"No records found in table '{table_name}'.")
            print("I will try to create a dummy record to see what happens, or check the table name.")
            # If no records exist, we can't easily see the fields via simple list
            # but usually the error message from a failed create tells us the valid fields!
    except Exception as e:
        print("Error probing Airtable:", e)

if __name__ == "__main__":
    probe()
