from pydantic import BaseModel, Field
from datetime import datetime
    
class Error(BaseModel):
    """Pydantic model for error records"""
    user_id: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for MongoDB storage"""
        return self.model_dump()