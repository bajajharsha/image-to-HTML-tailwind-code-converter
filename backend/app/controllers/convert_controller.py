import os
import time
import asyncio
import traceback

from pathlib import Path
from fastapi import Depends, UploadFile, File, Form

from backend.app.models.domain.error import Error
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.error_repository import ErrorRepo
from backend.app.usecases.combined_html.combine_html_usecase import CombineHtmlUsecase
from backend.app.usecases.single_image_usecase.single_image_usecase import SingleImageUsecase
from backend.app.usecases.image_segmentation.image_segmentation_usecase import ImageSegmentationUsecase


class ConvertController:
    def __init__(
        self,
        segmentation_usecase: ImageSegmentationUsecase = Depends(),
        combine_html_usecase: CombineHtmlUsecase = Depends(),
        single_image_usecase: SingleImageUsecase = Depends(),
        error_repo: ErrorRepo = Depends(),

    ):
        self.segmentation_usecase = segmentation_usecase
        self.combine_html_usecase = combine_html_usecase
        self.single_image_usecase = single_image_usecase
        self.error_repo = error_repo

    async def convert_image(self, image: UploadFile = File(...), use_heuristic: bool = Form(...)):
        """
        Main controller method to convert an uploaded image
        
        :param image: The uploaded image file
        :param use_heuristic: Flag to indicate whether to use heuristic methods
        
        :return: Dictionary with processing results
        """
        try:
            start_time = time.time()
            request_id = request_context.get()
            
            upload_dir = Path(f"uploads/{request_id}")
            images_dir = upload_dir / "images"
            os.makedirs(images_dir, exist_ok=True)
            
            segmentation_result = await self.segmentation_usecase.execute(image)
            
            image_files = [f for f in os.listdir(images_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

            is_multiple = True

            if len(image_files) == 1:
                is_multiple = False

            if not image_files:
                raise JsonResponseError(
                    status_code=500,
                    detail="No segmented images or original images found to process."
                )
                
            tasks = [self.single_image_usecase.execute(image_path = img_file, is_multiple = is_multiple, use_heuristic = use_heuristic)
                for img_file in image_files
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions = True)
            
            if is_multiple:
                print("\n🔗 PHASE 4: HTML Output")
                output_file_path, code = await self.combine_html_usecase.execute()
                end_time = time.time()
                print("Output file path:", output_file_path)
                print(f"Total time taken: {end_time - start_time} seconds")
                
                final_result = {
                    "request_id": request_id,
                    "output_file_path": output_file_path,
                    "code": code,
                }
                
                return final_result
            
            else:
                end_time = time.time()
                
                print(f"Total time taken: {end_time - start_time} seconds")
                return {
                    "request_id": request_id,
                    "code": results[0]["code"],
                }
            
        except Exception as e:

            tb = traceback.format_exc()
            
            print(f"ERROR in convert_image: {str(e)}")
            print(f"TRACEBACK: {tb}")

            await self.error_repo.insert_error(
                Error(
                    user_id=request_id,
                    error_message=f"[ERROR] occured while processing file in convert_image: {str(e)} \nTraceback: {tb}\nError from convert_controller in convert_image()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Image conversion failed: {str(e)}",
                original_exception=e
            ) from e
            
            
    async def convert_image_stream(self, image: UploadFile = File(...), use_heuristic: bool = Form(...)):
        """
        Main controller method to convert an uploaded image with streaming response
        
        :param image: The uploaded image file
        :param use_heuristic: Flag to indicate whether to use heuristic methods
        
        :return: Streaming response with processing results
        """
        try:
            request_id = request_context.get()
            
            upload_dir = Path(f"uploads/{request_id}")
            images_dir = upload_dir / "images"
            os.makedirs(images_dir, exist_ok=True)
            
            yield {"phase": "analyzing", "message": "🔍 Analyzing image structure...", "sequence": 1}
            segmentation_result = await self.segmentation_usecase.execute(image)
            yield {"phase": "analyzing", "message": "Initial analysis done, now proceeding towards processing...", "sequence": 2}

            yield {"phase": "processing", "message": "⚙️ Processing image elements...", "sequence": 3}
            
            image_files = [f for f in os.listdir(images_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]

            is_multiple = True

            if len(image_files) == 1:
                is_multiple = False

            if not image_files:
                raise JsonResponseError(
                    status_code=500,
                    detail="No segmented images or original images found to process."
                )
            
            if is_multiple:
                tasks = [self.single_image_usecase.execute(image_path = img_file, is_multiple = is_multiple, use_heuristic = use_heuristic)
                    for img_file in image_files
                ]
                
                await asyncio.gather(*tasks, return_exceptions = True)
            else:
                async for chunk in self.single_image_usecase.execute_single_stream(image_path=image_files[0], use_heuristic = use_heuristic):
                    yield chunk
                    
                yield {"phase":"individual sections","message":"✅ Code Generation completed...", "sequence": 4}
                
            if is_multiple:
                yield {"phase": "processing", "message": "Image processing Done, Proceeding with HTML conversion now...", "sequence": 5}
                yield {"phase": "generating", "message": "💻 Generating HTML code...", "sequence": 6}
                yield {"phase": "generating", "message": "⚙️ Converting visual elements to code structures...", "sequence": 7}
                
                print("\n🔗 PHASE 4: HTML Output")
                async for chunk in self.combine_html_usecase.execute_stream():
                    yield chunk
                    
                yield {"phase": "finalizing", "message": "✅ Code Generation completed...", "sequence": 8}
            
        except Exception as e:
            tb = traceback.format_exc()

            print(f"ERROR in convert_image_stream: {str(e)}")
            print(f"TRACEBACK: {tb}")

            await self.error_repo.insert_error(
                Error(
                    user_id=request_id,
                    error_message=f"[ERROR] occured while processing file in convert_image: {str(e)} \nTraceback: {tb}\nError from convert_controller in convert_image()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Image conversion failed: {str(e)}",
                original_exception=e

            )from e
                    