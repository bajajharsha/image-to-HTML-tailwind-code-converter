import os
import re
import traceback

from fastapi import Depends

from backend.app.models.domain.error import Error
from backend.app.utils.parsing_util import extract_html
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.error_repository import ErrorRepo
from backend.app.services.gemini_service import GeminiAPIService
from backend.app.prompts.combine_html_prompt import COMBINED_PROMPT


class CombineHtmlHelper:
    def __init__(self, gemini_service: GeminiAPIService = Depends(), error_repo: ErrorRepo = Depends()):
        self.gemini_service = gemini_service
        self.error_repo = error_repo
        self.request_id = request_context.get()

    def extract_html_section_number(self, file_path):
        """
        Extract section number from HTML filename.
        
        :param file_path: Path to the HTML file.
        
        :return: Section number as an integer.
        """
        filename = os.path.basename(str(file_path))
        match = re.search(r"section_(\d+)", filename)
        if match:
            return int(match.group(1))
        return 0


    def extract_image_number(self, file_path):
        """
        Extract image number from image filename.
        
        :param file_path: Path to the image file.
        
        :return: Image number as an integer.
        """
        filename = os.path.basename(str(file_path))
        match = re.search(r"(\d+)(?=\.[^.]+$)", filename)
        if match:
            return int(match.group(1))
        return 0
    

    async def combine_html_with_gemini(self, html_files, image_files=None):
        """
        Use Gemini to combine HTML files with optional image references.
        
        :param html_files: Dictionary of HTML files with their content.
        :param image_files: Dictionary of image files with their paths.
        
        :return: Tuple of parsed HTML and the original response from Gemini.
        """
        try:
            previous_code = ""
            for i, html_code in enumerate(html_files.values()):
                previous_code += f"HTML SECTION: {i + 1}\n```html\n{html_code}\n```\n"

            len_html_files = len(html_files.values())

            prompt_text = COMBINED_PROMPT.format(
                len_html_files=len_html_files, previous_code=previous_code
            )

            if image_files and len(image_files) > 0:
                image_paths = list(image_files.keys())

            response = await self.gemini_service.generate_content_with_image(
                prompt_text, image_paths
            )
            parsed_response = extract_html(response)

            return parsed_response, response
        
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=request_context.get(),
                    error_message=f"[ERROR] occurred while processing combine_html: {str(e)} \nTraceback: {tb} \nError from combine_html helper in combine_html_with_gemini()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error in combine_html_with_gemini: {str(e)}",
            )

    async def combine_html_with_gemini_stream(self, html_files, image_files=None):
        """
        Use Gemini to combine HTML files with optional image references in a streaming manner.
        
        :param html_files: Dictionary of HTML files with their content.
        :param image_files: Dictionary of image files with their paths.
        
        :return: Generator yielding chunks of the combined HTML content.
        """
        try:
            previous_code = ""
            for i, html_code in enumerate(html_files.values()):
                previous_code += f"HTML SECTION: {i + 1}\n```html\n{html_code}\n```\n"

            len_html_files = len(html_files.values())

            prompt_text = COMBINED_PROMPT.format(
                len_html_files=len_html_files, previous_code=previous_code
            )

            if image_files and len(image_files) > 0:
                image_paths = list(image_files.keys())
            
            async for chunk in self.gemini_service.generate_stream_content_with_image(prompt_text, image_paths):
                yield chunk
                
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=request_context.get(),
                    error_message=f"[ERROR] occurred while processing combine_html: {str(e)} \nTraceback: {tb} \nError from combine_html helper in combine_html_with_gemini()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error in combine_html_with_gemini: {str(e)}",
            )
