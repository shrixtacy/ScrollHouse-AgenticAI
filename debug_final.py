import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

def debug_final():
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
    
    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    # We KNOW "Client Name" and "Status" should work according to the earlier successful probe.
    # We will try to add the links with various names.
    drive_vars = ["google_drive_link", "Google Drive Link", "Google drive link", "drive_link", "Drive Link", "Drive"]
    notion_vars = ["notion_page_link", "notion_link", "Notion Hub Link", "Notion page link", "Notion Link", "Notion Hub", "Notion"]

    print(f"Brute-forcing link columns in table '{table_name}'...")
    
    for d_var in drive_vars:
        for n_var in notion_vars:
            try:
                # Try to create a record with both. If it works, we found the pair!
                table.create({
                    "Client Name": f"Test {d_var}/{n_var}",
                    d_var: "https://test-drive.com",
                    n_var: "https://test-notion.com"
                })
                print(f"SUCCESS! Found working columns: '{d_var}' and '{n_var}'")
                return
            except Exception as e:
                # If it's a 422, it means one of those names is wrong.
                continue

if __name__ == "__main__":
    debug_final()
