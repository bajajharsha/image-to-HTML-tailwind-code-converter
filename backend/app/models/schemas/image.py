from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from .base import BaseSchema, ResponseStatus

class ConversionResponse(BaseSchema):
    """Schema for conversion API response"""
    message: str
    code: str
    request_id: Optional[str] = None
    output_file_path: Optional[str] = None
    
class ConversionResult(BaseSchema):
    """Schema for internal conversion result"""
    success: bool = True
    request_id: Optional[str] = None
    code: str
    file_path: Optional[str] = None