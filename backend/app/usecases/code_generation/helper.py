import os
import sys
import json
import aiofiles
import traceback

from pathlib import Path
from typing import Dict, Any

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, project_root)

from fastapi import Depends

from backend.app.models.domain.error import Error
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.error_repository import ErrorRepo
from backend.app.prompts.code_generation_prompt import NON_HEURISTICS_GENERATE_CODE, HEURISTICS_GENERATE_CODE


class CodeGenerationHelper:
    """Helper class for UI code generation operations"""
    
    def __init__(
        self,
        error_repo: ErrorRepo = Depends()
    ):
        self.error_repo = error_repo
    
    def create_prompt(self, ui_data: dict, use_heuristic: bool) -> str:
        """
        Create a prompt for code generation based on the provided UI data.
        
        :param ui_data: UI data to generate code for
        :param use_heuristic: Flag to indicate if heuristic generation is used
        
        :return: Generated prompt string
        """
        if use_heuristic:
            return HEURISTICS_GENERATE_CODE.format(description = json.dumps(ui_data, indent=2))
        else:
            return NON_HEURISTICS_GENERATE_CODE.format(
            description=json.dumps(ui_data, indent=2)
        )
    
    async def save_generated_code(
        self,
        output_dir: Path,
        file_name: str,
        html_code: str
        ) -> Dict[str, Any]:
        """
        Save the generated code to a file.
        
        :param output_dir: Directory to save the generated code
        :param file_name: Name of the file to save the generated code
        :param html_code: Generated HTML code to save
        
        :return: Dictionary containing success status and file path
        """
        try:
            print(f"Saving generated code to {output_dir}/{file_name}")
            os.makedirs(output_dir, exist_ok=True)
            
            file_path = output_dir / file_name
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(html_code)
                
            return {
                "success": True,
                "file_path": str(file_path),
                "request_id": request_context.get() if request_context.get() else None
            }
            
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=request_context.get(),
                    error_message=f"[ERROR] occurred while saving generated code: {str(e)} \nTraceback: {tb} \nError from code_generation_helper in save_generated_code()"
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Failed to save generated code: {str(e)}"
            )