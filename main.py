from fastapi import FastAPI, Request
from pymongo import MongoClient
from datetime import datetime
import os
import requests

app = FastAPI(title="RVH CRM Backend")

# MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["rvh_crm"]
leads = db["leads"]

# AiSensy
AISENSY_API_KEY = os.getenv("AISENSY_API_KEY")
AISENSY_INSTANCE_ID = os.getenv("AISENSY_INSTANCE_ID")

def lead_score(data):
    score = 0
    if data.get("callerType") == "vet":
        score += 5
    if data.get("callerType") == "farmer":
        score += 4
    if data.get("appInterest") == "high":
        score += 5
    if data.get("farmSize") == "large":
        score += 3
    return score

def send_whatsapp(number, message):
    url = f"https://backend.aisensy.com/campaign/t1/api/v2"
    payload = {
        "apiKey": AISENSY_API_KEY,
        "campaignName": "RVH App Followup",
        "destination": number,
        "userName": "RVH Lead",
        "templateParams": [],
        "source": AISENSY_INSTANCE_ID,
        "media": {},
        "buttons": [],
        "carouselCards": [],
        "location": {},
        "attributes": {},
        "paramsFallbackValue": {},
        "message": message
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("WhatsApp Response:", response.text)
    except Exception as e:
        print("WhatsApp Error:", str(e))

def generate_message(lead):
    if lead["callerType"] == "vet":
        return (
            "Doctor sahab 👨‍⚕️\n"
            "Rohit Veterinary House app se aap vaccination reminders, "
            "patient records aur online medicine ordering manage kar sakte hain.\n"
            "Apni practice ko digital banaiye 📲\n"
            "Download karein: https://www.rohitveterinary.com/"
        )
    elif lead["callerType"] == "farmer":
        return (
            "Namaste 🙏\n"
            "Farm management ab digital ho sakta hai.\n"
            "Vaccination aur deworming reminder miss nahi hoga ✅\n"
            "Nuksaan kam, profit zyada 📈\n"
            "Download karein: https://www.rohitveterinary.com/"
        )
    else:
        return (
            "Namaste 🐾\n"
            "Apne pet ke liye vaccination aur health reminder miss mat kariye.\n"
            "Rohit Veterinary House app install karein 📲\n"
            "Download: https://www.rohitveterinary.com/"
        )

@app.post("/webhook/vapi")
async def vapi_webhook(req: Request):
    payload = await req.json()
    structured = payload.get("analysis", {}).get("structuredData", {})
    lead = {
        "callId": payload.get("call", {}).get("id"),
        "phoneNumber": payload.get("call", {}).get("customer", {}).get("number"),
        "callerType": structured.get("callerType", "unknown"),
        "animalType": structured.get("animalType"),
        "intent": structured.get("intent"),
        "urgencyLevel": structured.get("urgencyLevel"),
        "appInterest": structured.get("appInterest"),
        "farmSize": structured.get("farmSize"),
        "callSummary": payload.get("analysis", {}).get("summary"),
        "score": 0,
        "createdAt": datetime.utcnow()
    }
    lead["score"] = lead_score(lead)
    leads.insert_one(lead)
    if lead["phoneNumber"]:
        message = generate_message(lead)
        send_whatsapp(lead["phoneNumber"], message)
    return {"status": "stored and processed"}
