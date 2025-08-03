from pydantic import BaseModel, Field
from datetime import datetime
        
class LogData(BaseModel):
    """Pydantic model for LLM usage logs"""
    timestamp: datetime
    request_count: int
    input_tokens: int
    output_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    time_taken: float
    request_id: str
    provider: str

    def to_dict(self):
        """Convert to dictionary for MongoDB storage"""
        return self.model_dump()