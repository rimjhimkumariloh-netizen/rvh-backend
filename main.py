from fastapi import FastAPI, Request
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI(title="RVH CRM Backend")

client = MongoClient(os.getenv("MONGO_URI"))
db = client["rvh_crm"]
leads = db["leads"]

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

@app.post("/webhook/vapi")
async def vapi_webhook(req: Request):
    payload = await req.json()
    
    lead = {
        "callId": payload.get("callId"),
        "phoneNumber": payload.get("customer", {}).get("number"),
        "callerType": payload.get("structuredData", {}).get("callerType"),
        "animalType": payload.get("structuredData", {}).get("animalType"),
        "intent": payload.get("structuredData", {}).get("intent"),
        "urgencyLevel": payload.get("structuredData", {}).get("urgencyLevel"),
        "appInterest": payload.get("structuredData", {}).get("appInterest"),
        "farmSize": payload.get("structuredData", {}).get("farmSize"),
        "callSummary": payload.get("summary"),
        "score": 0,
        "createdAt": datetime.utcnow()
    }
    
    lead["score"] = lead_score(lead)
    leads.insert_one(lead)
    
    # WhatsApp trigger placeholder
    if lead["score"] >= 7:
        print("🔥 High-value lead – trigger WhatsApp follow-up")
    
    return {"status": "stored"}
