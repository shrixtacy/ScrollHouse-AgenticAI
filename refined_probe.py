import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

def refined_probe():
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
    
    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    try:
        records = table.all(max_records=5)
        if records:
            print(f"Field names found in existing records (wrapped in []):")
            # Collect all unique field names from the first few records
            all_fields = set()
            for r in records:
                all_fields.update(r['fields'].keys())
            
            for field in sorted(list(all_fields)):
                print(f"-[{field}]")
        else:
            print("No records found to probe field names.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    refined_probe()
