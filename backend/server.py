from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import requests
from pathlib import Path
from models import (
    AnalyticsTrack, AnalyticsRecord, AnalyticsStats,
    ContactMessage, ContactRecord, 
    NewsletterSubscribe, NewsletterRecord,
    SuccessResponse, ErrorResponse
)
from utils import get_ip_info, get_client_ip, sanitize_string
from collections import Counter
from datetime import datetime, timedelta
import tempfile

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Resume URL from the uploaded file
RESUME_URL = "https://customer-assets.emergentagent.com/job_college-ready/artifacts/eww3eu7g_Som%27s%20Linkedin%20profile.pdf"

# Original routes
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

# Analytics Routes
@api_router.post("/analytics/track")
async def track_analytics(analytics: AnalyticsTrack, request: Request):
    try:
        # Get client IP and location info
        client_ip = get_client_ip(request)
        ip_info = get_ip_info(client_ip)
        
        # Create analytics record
        record = AnalyticsRecord(
            sessionId=analytics.sessionId,
            page=analytics.page,
            timestamp=analytics.timestamp,
            userAgent=analytics.userAgent,
            ip=client_ip,
            country=ip_info["country"],
            city=ip_info["city"],
            referrer=analytics.referrer
        )
        
        # Save to database
        await db.analytics.insert_one(record.dict())
        
        return SuccessResponse(message="Analytics tracked successfully")
        
    except Exception as e:
        logger.error(f"Error tracking analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track analytics")

@api_router.get("/analytics/stats")
async def get_analytics_stats():
    try:
        # Get basic stats
        total_views = await db.analytics.count_documents({})
        unique_visitors = len(await db.analytics.distinct("sessionId"))
        
        # Get popular pages
        pipeline = [
            {"$group": {"_id": "$page", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        popular_pages_cursor = db.analytics.aggregate(pipeline)
        popular_pages = [{"page": doc["_id"], "views": doc["count"]} async for doc in popular_pages_cursor]
        
        # Get recent visitors (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_cursor = db.analytics.find(
            {"timestamp": {"$gte": yesterday}},
            {"country": 1, "city": 1, "timestamp": 1, "page": 1}
        ).sort("timestamp", -1).limit(20)
        recent_visitors = [doc async for doc in recent_cursor]
        
        # Get country stats
        country_cursor = db.analytics.find({}, {"country": 1})
        countries = [doc["country"] async for doc in country_cursor if doc.get("country") != "Unknown"]
        country_stats = dict(Counter(countries))
        
        return AnalyticsStats(
            totalViews=total_views,
            uniqueVisitors=unique_visitors,
            popularPages=popular_pages,
            recentVisitors=recent_visitors,
            countryStats=country_stats
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics stats")

# Contact Routes
@api_router.post("/contact")
async def submit_contact(contact: ContactMessage, request: Request):
    try:
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Sanitize input
        sanitized_message = sanitize_string(contact.message, 5000)
        sanitized_subject = sanitize_string(contact.subject, 200)
        
        # Create contact record
        record = ContactRecord(
            firstName=contact.firstName,
            lastName=contact.lastName,
            email=contact.email,
            subject=sanitized_subject,
            message=sanitized_message,
            ip=client_ip
        )
        
        # Save to database
        await db.contacts.insert_one(record.dict())
        
        logger.info(f"New contact message from {contact.email}: {contact.subject}")
        
        return SuccessResponse(
            message="Thank you for your message! Som will get back to you within 24-48 hours.",
            data={"submitted": True}
        )
        
    except Exception as e:
        logger.error(f"Error submitting contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit contact message")

@api_router.get("/contact/messages")
async def get_contact_messages():
    """Admin endpoint to get all contact messages"""
    try:
        cursor = db.contacts.find({}).sort("timestamp", -1).limit(100)
        messages = [doc async for doc in cursor]
        return SuccessResponse(message="Contact messages retrieved", data={"messages": messages})
        
    except Exception as e:
        logger.error(f"Error getting contact messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get contact messages")

# Resume Download Route
@api_router.get("/resume/download")
async def download_resume():
    try:
        # Download the file from the URL
        response = requests.get(RESUME_URL, stream=True)
        response.raise_for_status()
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        
        # Write the content to temp file
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        
        temp_file.close()
        
        # Return the file as a download
        return FileResponse(
            path=temp_file.name,
            filename="Som_Sengupta_Resume.pdf",
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Som_Sengupta_Resume.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download resume")

# Newsletter Routes
@api_router.post("/newsletter/subscribe")
async def subscribe_newsletter(newsletter: NewsletterSubscribe, request: Request):
    try:
        # Check if already subscribed
        existing = await db.newsletter.find_one({"email": newsletter.email})
        if existing:
            return SuccessResponse(message="You are already subscribed to our newsletter!")
        
        # Create newsletter record
        record = NewsletterRecord(
            email=newsletter.email,
            name=newsletter.name
        )
        
        # Save to database
        await db.newsletter.insert_one(record.dict())
        
        return SuccessResponse(message="Thank you for subscribing to our newsletter!")
        
    except Exception as e:
        logger.error(f"Error subscribing to newsletter: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to subscribe to newsletter")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()