import json
import time 
import base64
import traceback

from PIL import Image
from google import genai
from fastapi import Depends
from datetime import datetime
from google.genai import types

from backend.app.config.settings import settings
from backend.app.models.domain.log_data import LogData
from backend.app.services.api_service import ApiService
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.llm_usage_repository import LLMUsageRepository

class GeminiAPIService:
    def __init__(
        self, 
        api_service: ApiService = Depends(), 
        llm_usage_repo: LLMUsageRepository = Depends()
    ):
        self.api_key = settings.GEMINI_API_KEY
        self.url = f"{settings.GEMINI_URL}{self.api_key}"
        self.stream_url = f"{settings.GEMINI_STREAM_URL}{self.api_key}"
        self.api_service = api_service
        self.request_id = request_context.get()
        self.llm_usage_repo = llm_usage_repo
        self.chunk_llm_request_count = 0
        self.chunk_total_input_tokens = 0
        self.chunk_total_output_tokens = 0
        self.google_client = genai.Client(api_key=self.api_key)

    async def generate_content_with_image(
        self, prompt: str, image_paths: str, temperature: float = 0.1
    ) -> str:
        """
        Generates content using the Gemini API with an image and a prompt.
        
        :param prompt: The text prompt to send to the API.
        :param image_paths: The path(s) to the image file(s).
        :param temperature: The temperature setting for the generation.
            
        :return: The generated content from the API.
        """
        try:
            parts = []
        
            if isinstance(image_paths, list):
                for image_path in image_paths:
                    with open(image_path, "rb") as image_file:
                        image_bytes = image_file.read()
                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                    
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/png" if image_path.endswith(".png") else "image/jpeg",
                            "data": image_base64,
                        }
                    })
            else:
    
                image_path = image_paths
                with open(image_path, "rb") as image_file:
                    image_bytes = image_file.read()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                
                parts.append({
                    "inline_data": {
                        "mime_type": "image/png" if image_path.endswith(".png") else "image/jpeg",
                        "data": image_base64,
                    }
                })

            parts.append({"text": prompt})

            headers = {"Content-Type": "application/json"}

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/png"
                                    if image_path.endswith(".png")
                                    else "image/jpeg",
                                    "data": image_base64,
                                }
                            },
                            {"text": prompt},
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 40000,
                },
            }

            response_data = await self.api_service.post(
                self.url, headers=headers, data=payload
            )
   
            input_tokens = response_data.get("usageMetadata", {}).get("promptTokenCount", 0)
            output_tokens = response_data.get("usageMetadata", {}).get("candidatesTokenCount", 0)

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
                    provider="gemini-2.5-pro-preview-03-25",
                )
            )
            
            try:
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                raise JsonResponseError(
                    status_code=500,
                    detail="Unexpected response format from Gemini API.",
                )

        except FileNotFoundError:
            raise JsonResponseError(
                status_code=404, detail=f"Image file not found: {image_path}"
            )
            
        except Exception as e:
            tb = traceback.format_exc()
            print(f"ERROR in generate_content_with_image: {str(e)}")
            print(f"TRACEBACK: {tb}")
            raise JsonResponseError(
                status_code=500, detail=f"Error processing Gemini API request: {str(e)}"
            )
            
    async def generate_stream_content_with_image(
        self, prompt: str, image_paths: str, temperature: float = 0.1
    ):
        """
        Generates content using the Gemini API with an image and a prompt in streaming mode.
        
        :param prompt: The text prompt to send to the API.
        :param image_paths: The path(s) to the image file(s).
        :param temperature: The temperature setting for the generation.
        
        :return: A generator yielding the generated content from the API.
        """
        try:
            contents = []
            if isinstance(image_paths, list):
                for image_path in image_paths:
                    img = Image.open(image_path)
                    contents.append(img)
            else:
            
                img = Image.open(image_paths)
                contents.append(img)
                
            contents.append(prompt)

            # headers = {"Content-Type": "application/json"}
            
            # payload = {
            #     "contents": [
            #         {
            #             "parts": [
            #                 {
            #                     "inline_data": {
            #                         "mime_type": "image/png"
            #                         if image_path.endswith(".png")
            #                         else "image/jpeg",
            #                         "data": image_base64,
            #                     }
            #                 },
            #                 {"text": prompt},
            #             ],
            #         }
            #     ],
            #     "generationConfig": {
            #         "temperature": temperature,
            #         "maxOutputTokens": 40000,
            #     },
            # }
            
            
            # async for chunk in self.api_service.post_stream(self.stream_url, headers=headers, data=payload):
            #     if chunk.startswith("data: "):
            #         chunk = chunk[6:]
            #         if chunk == "[DONE]":
            #             break
            #         try:
            #             chunk_data = json.loads(chunk)
            #             text_chunk = chunk_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            #             if text_chunk:
            #                 yield text_chunk
                            
            #             usage_metadata = chunk_data.get("usageMetadata")
            #             if usage_metadata:
            #                 input_tokens = usage_metadata.get("promptTokenCount", 0)
            #                 output_tokens = usage_metadata.get("candidatesTokenCount", 0)

            #                 # Update cumulative counts
            #                 self.chunk_llm_request_count += 1
            #                 self.chunk_total_input_tokens += input_tokens
            #                 self.chunk_total_output_tokens += output_tokens

            #                 log_data = LogData(
            #                     timestamp=time.time(),
            #                     request_count=self.chunk_llm_request_count,
            #                     input_tokens=input_tokens,
            #                     output_tokens=output_tokens,
            #                     total_input_tokens=self.chunk_total_input_tokens,
            #                     total_output_tokens=self.chunk_total_output_tokens,
            #                     time_taken=time.time(),
            #                     request_id=self.request_id,
            #                     provider="gemini-2.5-pro-preview-03-25",
            #                 )

            #                 await self.llm_usage_repo.save_usage(log_data)
                        
            #         except (json.JSONDecodeError, KeyError, IndexError) as e:
            #             print(f"Error processing chunk: {str(e)}")

            response = self.google_client.models.generate_content_stream(
                model="gemini-2.5-pro-preview-03-25",
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=40000,
                )
            )

            for chunk in response:
                yield chunk.text

                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata is not None:
                    input_tokens = 0
                    output_tokens = 0
                    
                    if chunk.usage_metadata.prompt_token_count:
                        input_tokens = chunk.usage_metadata.prompt_token_count
                    
                    if chunk.usage_metadata.candidates_token_count:
                        output_tokens = chunk.usage_metadata.candidates_token_count
                    
                    self.chunk_llm_request_count += 1
                    self.chunk_total_input_tokens += input_tokens
                    self.chunk_total_output_tokens += output_tokens
                    
                    log_data = LogData(
                        timestamp=datetime.now(),
                        request_count=self.chunk_llm_request_count,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_input_tokens=self.chunk_total_input_tokens,
                        total_output_tokens=self.chunk_total_output_tokens,
                        time_taken=time.time(),
                        request_id=self.request_id,
                        provider="gemini-2.5-pro-preview-03-25",
                    )
                    
                    await self.llm_usage_repo.save_usage(log_data)
                        
        except FileNotFoundError:
            raise JsonResponseError(
                status_code=404, detail=f"Image file not found: {image_path}"
            )
            
        except Exception as e:
            tb = traceback.format_exc()
            print(f"ERROR in generate_stream_content_with_image: {str(e)}")
            print(f"TRACEBACK: {tb}")
            raise JsonResponseError(
                status_code=500, detail=f"Error processing Gemini API request: {str(e)}"
            )