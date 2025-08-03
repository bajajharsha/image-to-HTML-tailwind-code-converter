import time
import base64

from fastapi import Depends
from datetime import datetime

from backend.app.config.settings import settings
from backend.app.models.domain.log_data import LogData
from backend.app.services.api_service import ApiService
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.llm_usage_repository import LLMUsageRepository


class ClaudeService:
    def __init__(
        self,
        llm_usage_repo: LLMUsageRepository = Depends()
    ):
        self.api_key = settings.CLAUDE_API_KEY
        self.api_service = ApiService()
        self.url = settings.CLAUDE_URL
        self.request_id = request_context.get()
        self.llm_usage_repo = llm_usage_repo
        self.chunk_llm_request_count = 0
        self.chunk_total_input_tokens = 0
        self.chunk_total_output_tokens = 0

    async def generate_content(self, prompt: str, image_path: str, system_prompt: str) -> str:
        """
        Generates content using the Claude API by sending a prompt and an image.
        
        :param prompt: The text prompt to send to the API.
        :param image_path: The path to the image file.
        :param system_prompt: The system prompt to send to the API.
        
        :return: The generated content from the API.
        """
        try:
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()

            mime_type = "image/jpeg"
            if image_path.lower().endswith(".png"):
                mime_type = "image/png"

            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            message_content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_base64
                    }
                }
            ]

            payload = {
                "model": "claude-3-7-sonnet-20250219",
                "max_tokens": 10000,
                "temperature": 0.2,
                "messages": [
                    {"role": "user", "content": message_content}
                ],
                "system": system_prompt
            }

            response_data = await self.api_service.post(
                self.url, headers=headers, data=payload
            )
            
            usage = response_data["usage"]
            input_tokens = usage["input_tokens"]
            output_tokens = usage["output_tokens"]
            
            self.chunk_llm_request_count += 1
            self.chunk_total_input_tokens += input_tokens
            self.chunk_total_output_tokens += output_tokens
            
            await self.llm_usage_repo.save_usage(
                LogData(
                    timestamp=datetime.now(),
                    request_count=self.chunk_llm_request_count,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_input_tokens=self.chunk_total_input_tokens,
                    total_output_tokens=self.chunk_total_output_tokens,
                    time_taken=time.time(),
                    request_id=self.request_id,
                    provider="claude-3-7-sonnet-20250219",
                )
            )

            try:
                return response_data
            except (KeyError, IndexError):
                raise JsonResponseError(
                    status_code=500,
                    detail="Unexpected response format from Claude API."
                )

        except Exception as e:
            raise JsonResponseError(
                status_code=500, 
                detail=f"Error processing Claude API request: {str(e)}"
            )