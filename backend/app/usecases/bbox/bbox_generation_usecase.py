import os
import uuid
import traceback

from pathlib import Path
from fastapi import Depends

from backend.app.models.domain.error import Error
from backend.app.usecases.bbox.helper import BboxHelper
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.repositories.error_repository import ErrorRepo


class BboxUsecase:
    def __init__(
        self,
        bbox_helper: BboxHelper = Depends(),
        error_repo: ErrorRepo = Depends(),
    ):
        self.bbox_helper = bbox_helper
        self.request_id = request_context.get()
        self.error_repo = error_repo
        

    async def execute(self, img_path, use_heuristic: bool = False):
        """
        Execute the bounding box generation process.
        
        :param img_path: Path to the image file.
        :param use_heuristic: Flag to determine if heuristic method should be used.
        
        :return: Dictionary containing success status, request ID, and output path.
        """
        try:
        
            self.request_id = request_context.get() or str(uuid.uuid4())
            
            response_text = await self.bbox_helper.generate_bounding_boxes(img_path, use_heuristic)

            if use_heuristic:
                parsed_response = await self.bbox_helper.parse_gemini_response_for_heuristic(response_text)
                filtered_components = parsed_response
            else:
                parsed_response = await self.bbox_helper.parse_gemini_response(response_text)
                filtered_components = self.bbox_helper.filter_nested_elements(parsed_response)

            img_with_boxes = await self.bbox_helper.draw_bboxes(img_path, filtered_components, use_heuristic)
            
            img_name = os.path.splitext(os.path.basename(img_path))[0]
            project_root = Path(__file__).parent.parent.parent.parent.parent

            output_dir = f"{project_root}/uploads/{self.request_id}/labels"
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/{img_name}.json"
            output_img_path = f"{project_root}/uploads/{self.request_id}/images/bboxes"
            os.makedirs(output_img_path, exist_ok=True)
            output_img = Path(output_img_path, f"{img_name}.jpg")

            if img_with_boxes.mode == "RGBA":
                img_with_boxes = img_with_boxes.convert("RGB")
            
            img_with_boxes.save(output_img)

            # if use_heuristic:
            #     await self.bbox_helper.save_components_to_json_heu(filtered_components, output_path)
            # else:
            #     await self.bbox_helper.save_components_to_json(filtered_components, output_path)

            save_method = self.bbox_helper.save_components_to_json_heu if use_heuristic else self.bbox_helper.save_components_to_json

            await save_method(filtered_components, output_path)
            
            return {
                "success": True,
                "request_id": self.request_id,
                "output_path": output_path
            }
        
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occured while processing bounding box : {str(e)} \nTraceback: {tb} \nError from bbox_generation_usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error processing bounding box generation: {str(e)}",
                original_exception=e
            ) from e


