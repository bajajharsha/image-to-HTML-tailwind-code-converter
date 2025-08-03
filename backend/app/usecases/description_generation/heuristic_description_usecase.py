import os
import json
from pathlib import Path

from fastapi import Depends, HTTPException

from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError
from backend.app.usecases.description_generation.helper import DescriptionHelper

class HeuristicDescriptionUsecase:
    def __init__(self, description_helper: DescriptionHelper = Depends()):
        self.request_id = request_context.get()
        self.helper = description_helper
        self.helper.request_id = self.request_id

    async def execute(self, img_path) -> str:
        """
        Generate heuristic description for the given image.
        
        :param img_path: Path to the image file.
        
        :return: Path to the generated heuristic description JSON file.
        """
        try:
            os.makedirs(f"uploads/{self.request_id}", exist_ok= True)
            base_dir = Path(f"uploads/{self.request_id}")
            image_name = Path(os.path.basename(img_path))
            label_name = image_name.with_suffix(".json")

            label_path = Path(f"uploads/{self.request_id}/labels/{label_name}")

            if not label_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"No labels found for {self.request_id}",
                )
            
            with open(label_path, "r") as f:
                components = json.load(f)

            results_dir = os.path.join(base_dir, "description")
            os.makedirs(results_dir, exist_ok=True)
            des_name = image_name.with_suffix(".json")
            output_json_path = os.path.join(results_dir, des_name)
            medialess_path = os.path.join(results_dir, "medialess.jpg")

            hierarchy = self.helper.convert_json_structure(components, str(img_path))

            css_processed = self.helper.process_component_structure(hierarchy)

            final_structure = self.helper.extract_color_palettes(str(img_path), css_processed, str(medialess_path))

            with open(output_json_path, "w") as f:
                json.dump(final_structure, f, indent=2)

            print("Heuristic description generation completed successfully!")

            return str(output_json_path)
        
        except Exception as e:
            raise JsonResponseError(
                status_code=500,
                detail=f"Error in HeuristicDescriptionUsecase.execute: {str(e)}",
                original_exception=e
            ) from e
        




            