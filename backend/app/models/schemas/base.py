from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class BaseSchema(BaseModel):
    """Base schema with common configuration"""

    class Config:
        """Pydantic config"""
        populate_by_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }
        arbitrary_types_allowed = True
        
class ResponseStatus(BaseModel):
    """Standard status response included in all API responses"""
    success: bool = True
    message: Optional[str] = None