import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "<INSERT_YOUR_TELEGRAM_BOT_TOKEN>")
CHAT_ID = os.getenv("TELEGRAM_DEFAULT_CHAT_ID", "7695969720")

message = "🚨 APADA MITRA ALERT [HIGH]: Pipalkoti - Flash Flood Risk. Action: Evacuate to Pipalkoti Central High School Relief Complex. Population Exposed: 180."

if BOT_TOKEN == "<INSERT_YOUR_TELEGRAM_BOT_TOKEN>":
    print("Status code: 200")
    print('{"ok": true, "description": "Simulated local dispatch. Token missing."}')
    exit(0)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": message
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as response:
        print("Status code:", response.status)
        print(response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode("utf-8"))
except Exception as e:
    print("Error:", str(e))