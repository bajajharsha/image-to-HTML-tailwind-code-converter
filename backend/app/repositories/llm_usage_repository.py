from fastapi import Depends

from backend.app.models.domain.log_data import LogData
from backend.app.config.database import mongodb_database
from backend.app.utils.error_handler import JsonResponseError


class LLMUsageRepository:
    def __init__(
        self, collection=Depends(mongodb_database.get_llm_usage_collection)
    ) -> None:
        self.collection = collection

    async def save_usage(self, usage: LogData):
        """
        Save the LLM usage data to the database.
        
        :param usage: The LLM usage data to be saved.
        
        :return: The result of the insert operation.
        """
        insert_result = await self.collection.insert_one(usage.to_dict())
        if not insert_result.inserted_id:
            raise JsonResponseError(
                status_code=500,
                detail="Failed to insert complaint \n error from llm_usage_repository in save_usage()",
            )
            
        return insert_result
