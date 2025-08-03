import os
import json
import uuid
import traceback
from pathlib import Path
import asyncio
from PIL import Image

from fastapi import Depends, HTTPException

from backend.app.usecases.description_generation.helper import DescriptionHelper
from backend.app.services.claude_service import ClaudeService
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError

from backend.app.models.domain.error import Error
from backend.app.repositories.error_repository import ErrorRepo

class DescriptionGenerationUsecase:
    def __init__(
        self,
        claude_service: ClaudeService = Depends(),
        description_helper: DescriptionHelper = Depends(),
        error_repo: ErrorRepo = Depends(),
    ):
        self.request_id = request_context.get()
        self.helper = description_helper
        self.helper.request_id = self.request_id
        self.error_repo = error_repo
        self.claude_service = claude_service
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0

    async def execute(self, img_path, max_concurrent = 5) -> str:
        """
        Process an image to generate detailed descriptions of its components.
        
        :param img_path: Path to the image file.
        :param max_concurrent: Maximum number of concurrent tasks to run.
        
        :return: Path to the output JSON file containing detailed descriptions.
        """
        try:
            os.makedirs(f"uploads/{self.request_id}", exist_ok= True)
            base_dir = Path(f"uploads/{self.request_id}")
            image_name = Path(os.path.basename(img_path))
            label_name = image_name.with_suffix(".json")

            label_path = Path(f"uploads/{self.request_id}/labels/{label_name}")

            if not label_path.exists():
                await self.error_repo.insert_error(
                    Error(
                        user_id=request_context.get(),
                        error_message=f"[ERROR] occurred while processing description generation: No labels found \n error from description generation usecase in execute()",
                    )
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"No labels found for {self.request_id}",
                )
            
            with open(label_path, "r") as f:
                components = json.load(f)

            results_dir = os.path.join(base_dir, "description")
            os.makedirs(results_dir, exist_ok=True)
            des_path = image_name.with_suffix(".json")
            output_json_path = os.path.join(results_dir, des_path)

            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_with_semaphore(component, index):
                async with semaphore:
                    print(f"\n[{index+1}/{len(components)}] Processing {component['label']}...")
                    return await self._process_component_async(img_path, component, results_dir)
                
            tasks = [process_with_semaphore(component, i) for i, component in enumerate(components)]

            component_details_list = await asyncio.gather(*tasks)

            detailed_components = {details["id"]: details for details in component_details_list}

            with open(output_json_path, 'w') as f:
                json.dump(detailed_components, f, indent=2)

            self.total_input_tokens = self.helper.total_input_tokens
            self.total_output_tokens = self.helper.total_output_tokens
            self.total_tokens = self.helper.total_tokens

            print(f"\nDetailed component analysis complete! Saved to: {output_json_path}")
            print(f"Image assets saved to: {os.path.join(results_dir, 'assets', 'images')}")

            print("\nToken Usage Summary:")
            print(f"Total input tokens: {self.total_input_tokens}")
            print(f"Total output tokens: {self.total_output_tokens}")
            print(f"Total tokens: {self.total_tokens}")

            return str(output_json_path)
        
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occurred while processing description generation: {str(e)} \nTraceback: {tb} \nError from description generation usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error in DescriptionGenerationUsecase.execute: {str(e)}",
                original_exception=e
            ) from e
        

    async def _process_component_async(self, img_path, component, output_dir):
        """
        Asynchronously process a single component: highlight it, analyze it, and return the structured data.
        
        :param img_path: Path to the original image.
        :param component: The component to process, containing its label and bounding box.
        :param output_dir: Directory to save the processed images and results.
        
        :return: A dictionary containing the processed component's details.
        """
        component_id = str(uuid.uuid4())[:8]
        label = component["label"]
        box_2d = component["box_2d"]
        
        temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        result = {
            "id": component_id,
            "type": label,
            "coordinates": {},
            "description": [],
            "content":{},
            "media": {"images": [], "icons": []},
        }
        
        img = Image.open(img_path)
        img_width, img_height = img.size
        y_min, x_min, y_max, x_max = box_2d
        x1 = int(x_min * img_width / 1000)
        y1 = int(y_min * img_height / 1000)
        x2 = int(x_max * img_width / 1000)
        y2 = int(y_max * img_height / 1000)
        
        result["coordinates"] = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }
        
        if label.lower() == "image":
            image_path = self.helper.clip_and_save_image(img_path, box_2d, component_id, output_dir)
            
            result["type"] = "img"
            result["content"]["src"] = image_path
            result["media"]["images"].append({
                "id": component_id,
                "coordinates": result["coordinates"],
                "filePath": image_path,
                "role": "content",
                "description": "Image clipped from UI"
            })
            
            print(f"✓ [{component_id}] Saved image component to: {image_path}")
            
        else:
            temp_img_path = os.path.join(temp_dir, f"{component_id}_{label}.png")
            self.helper.highlight_component(img_path, box_2d, temp_img_path)
            
            component_data = await self.helper.analyze_component_with_claude_async(temp_img_path, label, component_id)
            if component_data is None:
                component_data = {
                    "description": ""
                }
            
            result.update({
                "description": component_data
            })
            
            media = component_data.get("media", {})
            if media is not None and isinstance(media, dict) and "images" in media and media["images"] is not None:
                for i, img_data in enumerate(media["images"]):
                    if img_data:
                        img_component_id = f"{component_id}_img_{i}"
                        img_data["id"] = img_component_id
                        img_data["detected"] = True
                        if "filePath" in img_data:
                            del img_data["filePath"]
        
        return result