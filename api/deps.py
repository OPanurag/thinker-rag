from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, validator
import httpx
import re

class URLValidationError(Exception):
    pass

class ContentType(str, Enum):
    HTML = "text/html"
    PLAIN = "text/plain"

class URLMetadata(BaseModel):
    url: HttpUrl
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    title: Optional[str] = None
    
    @validator('url')
    def validate_url_scheme(cls, v):
        if str(v).startswith(('http://', 'https://')):
            return v
        raise ValueError('URL must use HTTP or HTTPS scheme')

async def validate_url(url: str) -> URLMetadata:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.head(str(url), timeout=10.0)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not ('text/html' in content_type or 'text/plain' in content_type):
                raise URLValidationError(f"Unsupported content type: {content_type}")
            
            # Check content length if provided
            content_length = response.headers.get('content-length')
            if content_length:
                length = int(content_length)
                if length > 10 * 1024 * 1024:  # 10MB limit
                    raise URLValidationError("Content too large")
                
            # Basic metadata
            metadata = URLMetadata(
                url=url,
                content_type=content_type,
                content_length=int(content_length) if content_length else None
            )
            return metadata
            
    except httpx.HTTPStatusError as e:
        raise URLValidationError(f"HTTP error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise URLValidationError(f"Request error: {str(e)}")
    except Exception as e:
        raise URLValidationError(f"Validation error: {str(e)}")
