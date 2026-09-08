import os
import requests
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

response = requests.get(
    "https://content.twilio.com/v1/Content",
    auth=(account_sid, auth_token)
)

print("Status code:", response.status_code)
print(response.text)