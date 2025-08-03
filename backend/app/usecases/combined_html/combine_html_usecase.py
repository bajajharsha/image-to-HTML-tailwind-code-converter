import os
import asyncio
import traceback

from pathlib import Path
from fastapi import Depends, HTTPException

from backend.app.models.domain.error import Error
from backend.app.utils.parsing_util import extract_html
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.error_repository import ErrorRepo
from backend.app.services.gemini_service import GeminiAPIService
from backend.app.usecases.combined_html.helper import CombineHtmlHelper


class CombineHtmlUsecase:
    def __init__(
        self,
        gemini_service: GeminiAPIService = Depends(),
        combine_helper: CombineHtmlHelper = Depends(),
        error_repo: ErrorRepo = Depends(),
    ):
        self.gemini_service = gemini_service
        self.combine_helper = combine_helper
        self.error_repo = error_repo
        self.request_id = request_context.get()
        
    async def execute(self, output_filename: str = "index.html") -> str:
        """
        Combines HTML files and images into a single HTML file using Gemini API.
        
        :param output_filename: The name of the output HTML file.
        
        :return: The path to the combined HTML file.
        """
        try:
            base_dir = Path(f"uploads/{self.request_id}")
            code_dir = base_dir / "code_generation"
            images_dir = base_dir / "images"

            if not code_dir.exists():
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occurred while processing combine_html: Code generation directory not found \n error from combine_html usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"No code generation found for {self.request_id}",
                )
                
            html_files = list(code_dir.glob("*.html"))
            
            if not html_files:
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occurred while processing combine_html: No HTML files found \n error from combine_html usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=404, detail=f"No HTML files found for {self.request_id}"
                )

            image_files = []
            if images_dir.exists():
                image_files = list(images_dir.glob("*.png")) + \
                              list(images_dir.glob("*.jpg")) + \
                              list(images_dir.glob("*.jpeg")) + \
                              list(images_dir.glob("*.gif")) + \
                              list(images_dir.glob("*.bmp")) + \
                              list(images_dir.glob("*.tiff"))

            html_contents = {}
            for file_path in sorted(
                html_files, key=self.combine_helper.extract_html_section_number
            ):
                html_contents[str(file_path)] = file_path.read_text(encoding="utf-8")

            image_contents = {}
            if image_files:
                for file_path in sorted(
                    image_files, key=self.combine_helper.extract_image_number
                ):
                    image_contents[str(file_path)] = file_path.read_bytes()

            combined_html, response_text = await self.combine_helper.combine_html_with_gemini(
                html_contents, image_contents
            )

            if not combined_html:
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occurred while processing combine_html: Failed to generate combined HTML \n error from combine_html usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=500, detail="Failed to generate combined HTML"
                )

            os.makedirs(base_dir / "final", exist_ok=True)
            output_path = base_dir / "final" / output_filename
            output_path.write_text(combined_html, encoding="utf-8")

            return str(output_path), response_text
        
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occurred while processing combine_html: {str(e)} \nTraceback: {tb} \nError from combine_html usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error in CombineHtmlUsecase.execute: {str(e)}",
                original_exception=e
            ) from e


    async def execute_stream(self, output_filename: str = "index.html"):
        """
        Combines HTML files and images into a single HTML file using Gemini API with streaming.
        
        :param output_filename: The name of the output HTML file.
        
        :return: A generator yielding chunks of the combined HTML file.
        """
        try:
            base_dir = Path(f"uploads/{self.request_id}")
            code_dir = base_dir / "code_generation"
            images_dir = base_dir / "images"
            
            print(f"Code directory: {code_dir}")
            
            if not code_dir.exists():
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occurred while processing combine_html: Code generation directory not found \n error from combine_html usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"No code generation found for {self.request_id}",
                )
                
            html_files = list(code_dir.glob("*.html"))
            if not html_files:
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occurred while processing combine_html: No HTML files found \n error from combine_html usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=404, detail=f"No HTML files found for {self.request_id}"
                )
                
            html_files = list(code_dir.glob("*.html"))
            if not html_files:
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occurred while processing combine_html: No HTML files found \n error from combine_html usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=404, detail=f"No HTML files found for {self.request_id}"
                )
                
            image_files = []
            if images_dir.exists():
                image_files = list(images_dir.glob("*.png")) + \
                              list(images_dir.glob("*.jpg")) + \
                              list(images_dir.glob("*.jpeg")) + \
                              list(images_dir.glob("*.gif")) + \
                              list(images_dir.glob("*.bmp")) + \
                              list(images_dir.glob("*.tiff"))

            html_contents = {}
            for file_path in sorted(
                html_files, key=self.combine_helper.extract_html_section_number
            ):
                html_contents[str(file_path)] = file_path.read_text(encoding="utf-8")

            image_contents = {}
            if image_files:
                for file_path in sorted(
                    image_files, key=self.combine_helper.extract_image_number
                ):
                    image_contents[str(file_path)] = file_path.read_bytes()
                    
            complete_response = ""
            async for chunk in self.combine_helper.combine_html_with_gemini_stream(html_contents, image_contents):
                complete_response += chunk
                yield chunk
            
            parsed_response = extract_html(complete_response)
            
            if not parsed_response:
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occurred while processing combine_html: Failed to generate combined HTML \n error from combine_html usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=500, detail="Failed to generate combined HTML"
                )
                
            os.makedirs(base_dir / "final", exist_ok=True)
            output_path = base_dir / "final" / output_filename
            output_path.write_text(parsed_response, encoding="utf-8")
        
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occurred while processing combine_html: {str(e)} \nTraceback: {tb} \nError from combine_html usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error in CombineHtmlUsecase.execute: {str(e)}",
                original_exception=e
            ) from e