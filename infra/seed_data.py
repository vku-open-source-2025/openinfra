import urllib.request
import urllib.error
import json
import os
import uuid
import random
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8001/api"
CSV_FILE_PATH = "../sample_data.csv"

def upload_csv():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Error: File not found at {CSV_FILE_PATH}")
        return False

    print(f"Uploading {CSV_FILE_PATH}...")
    
    boundary = str(uuid.uuid4())
    data = []
    
    data.append(f'--{boundary}')
    data.append(f'Content-Disposition: form-data; name="file"; filename="sample_data.csv"')
    data.append('Content-Type: text/csv')
    data.append('')
    
    with open(CSV_FILE_PATH, 'rb') as f:
        data.append(f.read().decode('utf-8'))
        
    data.append(f'--{boundary}--')
    data.append('')
    
    body = '\r\n'.join(data).encode('utf-8')
    headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
    
    req = urllib.request.Request(f"{BASE_URL}/ingest/csv", data=body, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            print("CSV Upload Success:", response.read().decode('utf-8'))
            return True
    except urllib.error.URLError as e:
        print(f"CSV Upload Failed: {e}")
        return False

def get_assets():
    try:
        req = urllib.request.Request(f"{BASE_URL}/assets/?limit=1000")
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to fetch assets: {e}")
        return []

def generate_maintenance_logs(assets):
    print("Generating fake maintenance logs...")
    
    statuses = ["Pending", "In Progress", "Completed", "Scheduled"]
    technicians = ["Nguyen Van A", "Tran Thi B", "Le Van C", "Pham Thi D", "Hoang Van E"]
    descriptions = [
        "Routine inspection", "Replace broken component", "Safety check", 
        "Firmware update", "Cleaning and maintenance", "Emergency repair",
        "Voltage check", "Structural integrity assessment"
    ]
    
    logs_created = 0
    
    # Generate logs for 40% of assets
    target_assets = random.sample(assets, int(len(assets) * 0.4))
    
    for asset in target_assets:
        # Generate 1-3 logs per asset
        num_logs = random.randint(1, 3)
        
        for _ in range(num_logs):
            status = random.choice(statuses)
            scheduled_date = datetime.now() - timedelta(days=random.randint(0, 365))
            
            log_data = {
                "asset_id": asset["_id"],
                "description": random.choice(descriptions),
                "technician": random.choice(technicians),
                "status": status,
                "scheduled_date": scheduled_date.isoformat(),
                "completed_date": (scheduled_date + timedelta(hours=random.randint(1, 48))).isoformat() if status == "Completed" else None
            }
            
            req = urllib.request.Request(
                f"{BASE_URL}/maintenance/", 
                data=json.dumps(log_data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            try:
                urllib.request.urlopen(req)
                logs_created += 1
            except Exception as e:
                print(f"Failed to create log: {e}")

    print(f"Successfully created {logs_created} maintenance logs.")

if __name__ == "__main__":
    if upload_csv():
        assets = get_assets()
        if assets:
            generate_maintenance_logs(assets)
