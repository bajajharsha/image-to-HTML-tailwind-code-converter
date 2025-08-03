from backend.app.usecases.bbox.bbox_generation_usecase import BboxUsecase
from backend.app.usecases.description_generation.description_generation_usecase import DescriptionGenerationUsecase
from backend.app.usecases.description_generation.heuristic_description_usecase import HeuristicDescriptionUsecase
from backend.app.usecases.code_generation.code_generation_usecase import CodeGenerationUsecase
from fastapi import Depends, UploadFile, File
from backend.app.utils.error_handler import JsonResponseError
from backend.app.utils.context_util import request_context

import os
import asyncio
import traceback
from pathlib import Path

from backend.app.models.domain.error import Error
from backend.app.repositories.error_repository import ErrorRepo


class SingleImageUsecase:
    def __init__(
        self,
        bbox_usecase: BboxUsecase = Depends(),
        description_generation_usecase: DescriptionGenerationUsecase = Depends(),
        heuristic_description_usecase: HeuristicDescriptionUsecase = Depends(),
        code_generation_usecase: CodeGenerationUsecase = Depends(),
        error_repo: ErrorRepo = Depends(),
    ):
        self.bbox_usecase = bbox_usecase
        self.description_generation_usecase = description_generation_usecase
        self.heuristic_description_usecase = heuristic_description_usecase
        self.code_generation_usecase = code_generation_usecase
        self.request_id = request_context.get()
        self.error_repo = error_repo
    
    async def execute(self, image_path: str, is_multiple: bool = False, use_heuristic: bool = False):
        """
        Process a single image through all the required usecases
        
        :param image_path: Path to the image file relative to uploads/{request_id}/images/
        :param is_multiple: Flag to indicate if multiple images are being processed (default: False)
        :param use_heuristic: Flag to indicate if heuristic description generation should be used (default: False)
        
        :return: Dictionary with combined results from all processing steps
        """
        try:
            full_image_path = f"uploads/{self.request_id}/images/{image_path}"
            
            print(f"📋 Starting pipeline for image: {image_path}")
            print(f"\n🔍 PHASE 1: Component Detection for {image_path}")
            
            bbox_result = await self.bbox_usecase.execute(img_path = full_image_path, use_heuristic = use_heuristic)
            print(f"  ✓ Component data saved to: {bbox_result['output_path']}")
            
            print(f"\n🔬 PHASE 2: Component Details Analysis for {image_path}")
            if use_heuristic:
                print(use_heuristic)
                await self.heuristic_description_usecase.execute(img_path = full_image_path)
            else:
                await self.description_generation_usecase.execute(img_path = full_image_path)
            
            print(f"\n💻 PHASE 3: HTML Code Generation for {image_path}")
            code_generation_result = await self.code_generation_usecase.execute(image_file_path = image_path, is_multiple = is_multiple, use_heuristic = use_heuristic)
            print(f"  ✓ HTML code generated and saved to: {code_generation_result['file_path']}\n")
            
            return code_generation_result
            
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error processing image {image_path}: {str(e)}")
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occurred while processing image {image_path}: {str(e)} \nTraceback: {tb} \nError from single_image_usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error processing image {image_path}: {str(e)}",
                original_exception=e,
            ) from e
            
    async def execute_single_stream(self, image_path: str, use_heuristic: bool = False):
        """
        Process a single image through all the required usecases for streaming
        
        :param image_path: Path to the image file relative to uploads/{request_id}/images/
        :param use_heuristic: Flag to indicate if heuristic description generation should be used (default: False)
        
        :return: Generator yielding progress messages
        """
        try:
            yield "Processing your image..."
                
            full_image_path = f"uploads/{self.request_id}/images/{image_path}"
            
            print(f"📋 Starting pipeline for image: {image_path}")
            print(f"\n🔍 PHASE 1: Component Detection for {image_path}")
            
            bbox_result = await self.bbox_usecase.execute(img_path = full_image_path, use_heuristic = use_heuristic)
            print(f"  ✓ Component data saved to: {bbox_result['output_path']}")
            
            print(f"\n🔬 PHASE 2: Component Details Analysis for {image_path}")
            if use_heuristic:
                print(use_heuristic)
                await self.heuristic_description_usecase.execute(img_path = full_image_path)
            else:
                await self.description_generation_usecase.execute(img_path = full_image_path)
                
            yield "Done processing your image, now proceeding to convert it to HTML..."
            yield "💻 Generating HTML code..."
            yield "⚙️ Converting visual elements to code structures..."
            async for chunk in self.code_generation_usecase.execute_stream(image_file_path=image_path, is_multiple=False, use_heuristic = use_heuristic):
                yield chunk
            
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error processing image {image_path}: {str(e)}")
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occurred while processing image {image_path}: {str(e)} \nTraceback: {tb} \nError from single_image_usecase in execute_stream()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error processing image {image_path}: {str(e)}",
                original_exception=e
            ) from e