import os
import sys
import json
import asyncio
import aiofiles
import traceback
from pathlib import Path

project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))


from pathlib import Path
from fastapi import Depends
from typing import Dict, Any

from backend.app.models.domain.error import Error
from backend.app.utils.parsing_util import extract_html
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.error_repository import ErrorRepo
from backend.app.services.gemini_service import GeminiAPIService
from backend.app.usecases.code_generation.helper import CodeGenerationHelper


class CodeGenerationUsecase:
    def __init__(self, gemini_service: GeminiAPIService = Depends(), code_generation_helper: CodeGenerationHelper = Depends(), error_repo: ErrorRepo = Depends()):
        self.gemini_service = gemini_service
        self.code_generation_helper = code_generation_helper
        
        self.project_root = Path(__file__).resolve().parents[4]
        self.request_id = request_context.get()
        self.uploads_dir = self.project_root / "uploads" / self.request_id
        self.error_repo = error_repo
    
    async def execute(
        self, 
        image_file_path: str, 
        is_multiple: bool,
        use_heuristic: bool = False
    ) -> Dict[str, Any]:
        """
        Generate UI code from UI specifications and image.
        
        :param image_file_path: Path to the image file
        :param is_multiple: Whether this is part of multiple code generations
        :param use_heuristic: Whether to use heuristic for code generation
        
        :return: Dictionary containing the result of the code generation
        """
        try:
            
            if not os.path.exists(self.uploads_dir):
                os.makedirs(self.uploads_dir, exist_ok = True)
                print(f"Created uploads directory: {self.uploads_dir}")
                
            complete_image_path = self.uploads_dir / "images" / image_file_path
            print(f"Complete image path: {complete_image_path}")

            if not os.path.exists(complete_image_path):
                raise JsonResponseError(status_code=404, detail=f"Image file not found: {image_file_path}")
            
            json_file_path = f"{Path(image_file_path).stem}.json"
            complete_json_path = self.uploads_dir / "description" / json_file_path
            
            if not os.path.exists(complete_json_path):
                raise JsonResponseError(status_code=404, detail=f"Json file not found: {json_file_path}")
    
            async with aiofiles.open(complete_json_path, 'r') as file:
                ui_data = json.loads(await file.read())
            
            prompt = self.code_generation_helper.create_prompt(ui_data, use_heuristic)
            
            response_text = await self.gemini_service.generate_content_with_image(prompt, str(complete_image_path))
            
            html_code = extract_html(response_text = response_text)
            
            result = {
                "success": True,
                "request_id": request_context.get() if request_context.get() else None,
                "code": response_text,
            }
                
            file_name = f"{Path(image_file_path).stem}_gemini.html"
                
            if is_multiple:
                output_dir = self.uploads_dir / "code_generation"
            else:
                output_dir = self.uploads_dir / "final"
            save_result = await self.code_generation_helper.save_generated_code(output_dir, file_name, html_code)
            
            if save_result["success"]:
                result["file_path"] = save_result["file_path"]
            
            return result
            
        except JsonResponseError as e:
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occured while processing code generation : {e.detail} \n error from code_generation_usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=e.status_code,
                detail=f"Error processing Gemini API request: {e.detail}"
            )
            
        except Exception as e:
            tb = traceback.format_exc()
            error_message = str(e)
            await self.error_repo.insert_error(
                Error(
                    user_id=request_context.get(),
                    error_message=f"[ERROR] Failed to generate UI code : {error_message} \nTraceback: {tb}\nError from code_generation_usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Failed to generate UI code: {error_message}",
                original_exception=e
            ) from e
            
    async def execute_stream(
        self,
        image_file_path: str,
        is_multiple: bool,
        use_heuristic: bool = False
    ):
        """
        Generate UI code from UI specifications and image in a streaming manner.
        
        :param image_file_path: Path to the image file
        :param is_multiple: Whether this is part of multiple code generations
        :param use_heuristic: Whether to use heuristic for code generation
        
        :return: Generator yielding chunks of the generated code
        """
        try:
            if not os.path.exists(self.uploads_dir):
                os.makedirs(self.uploads_dir, exist_ok=True)
                
            complete_image_path = self.uploads_dir / "images" / image_file_path

            if not os.path.exists(complete_image_path):
                raise JsonResponseError(status_code=404, detail=f"Image file not found: {image_file_path}")
            
            json_file_path = f"{Path(image_file_path).stem}.json"
            complete_json_path = self.uploads_dir / "description" / json_file_path
            
            if not os.path.exists(complete_json_path):
                raise JsonResponseError(status_code=404, detail=f"Json file not found: {json_file_path}")

            async with aiofiles.open(complete_json_path, 'r') as file:
                ui_data = json.loads(await file.read())
                
            prompt = self.code_generation_helper.create_prompt(ui_data, use_heuristic)
            
            complete_response = ""
            async for chunk in self.gemini_service.generate_stream_content_with_image(prompt, str(complete_image_path)):
                complete_response += chunk
                yield chunk
                
            html_code = extract_html(response_text = complete_response)
                
            file_name = f"{Path(image_file_path).stem}_gemini.html"
                
            if is_multiple:
                output_dir = self.uploads_dir / "code_generation"
            else:
                output_dir = self.uploads_dir / "final"
            
            await self.code_generation_helper.save_generated_code(output_dir, file_name, html_code)
            
        except JsonResponseError as e:
            raise e
        
        except Exception as e:
            error_message = str(e)
            raise JsonResponseError(
                status_code=500,
                detail=f"Failed to generate UI code: {error_message}",
                original_exception=e
            ) from e
    