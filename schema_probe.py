import os
import requests
from dotenv import load_dotenv

load_dotenv()

def schema_probe():
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Clients")
    
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Try creating a record with a nonsense field to force an error that lists column names
    data = {"fields": {"ThisColumnDoesNotExist": "test"}}
    
    response = requests.post(url, headers=headers, json=data)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

if __name__ == "__main__":
    schema_probe()
