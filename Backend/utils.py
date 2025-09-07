import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

def get_ip_info(ip: str) -> Dict[str, str]:
    """Get country and city information from IP address using free service"""
    try:
        # Using ipapi.co free service (1000 requests/day)
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "country": data.get("country_name", "Unknown"),
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown")
            }
    except Exception as e:
        logger.warning(f"Failed to get IP info for {ip}: {str(e)}")
    
    return {
        "country": "Unknown",
        "city": "Unknown", 
        "region": "Unknown"
    }

def get_client_ip(request) -> str:
    """Extract client IP from request headers"""
    # Check for forwarded headers first (for proxy/load balancer scenarios)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, get the first one
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    client_host = getattr(request.client, "host", "127.0.0.1")
    return client_host if client_host != "testclient" else "127.0.0.1"

def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Basic string sanitization"""
    if not text:
        return ""
    
    # Remove any potentially harmful characters
    sanitized = text.replace("<", "&lt;").replace(">", "&gt;")
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    
    return sanitized.strip()