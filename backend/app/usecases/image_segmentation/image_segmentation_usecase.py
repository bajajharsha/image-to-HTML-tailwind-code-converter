import os
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import File, UploadFile
from PIL import Image

from backend.app.usecases.image_segmentation.helper import (
    enhanced_image_segmentation,
    split_image_into_sections,
)
from backend.app.utils.context_util import request_context
from backend.app.utils.error_handler import JsonResponseError

from backend.app.models.domain.error import Error
from backend.app.repositories.error_repository import ErrorRepo
from fastapi import Depends
class ImageSegmentationUsecase:
    def __init__(self, error_repo: ErrorRepo = Depends()):
        self.height_threshold = 1430
        self.confidence_threshold = 0.7
        self.min_line_distance = 0
        self.error_repo = error_repo


    async def execute(
        self,
        image_file: UploadFile = File(...),
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Process an uploaded image to determine if segmentation is needed and perform segmentation if necessary.

        :param image_file: The uploaded image file.
        :param output_dir: Optional directory to save the processed images. If not provided, a default directory will be used.
        
        :return: A dictionary containing the result of the image processing, including image dimensions, segmentation status, and file paths.
        """
        try:
            request_id = request_context.get()
            uploads_base_dir = Path(
                os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "../../../../uploads")
                )
            )

            if output_dir is None:
                output_dir = uploads_base_dir / request_id

            output_dir.mkdir(parents=True, exist_ok=True)

            images_dir = output_dir / "images"
            images_dir.mkdir(parents=True, exist_ok=True)

            file_name = image_file.filename or f"uploaded_image_{request_id}"
            temp_image_path = output_dir / f"temp_{file_name}"

            contents = await image_file.read()
            with open(temp_image_path, "wb") as f:
                f.write(contents)

            await image_file.seek(0)

            with Image.open(temp_image_path) as img:
                image_height = img.height
                image_width = img.width

            result = {
                "success": True,
                "image_height": image_height,
                "image_width": image_width,
                "request_id": request_id,
                "segmentation_performed": False,
                "segments": [],
            }

            needs_segmentation = image_height > self.height_threshold

            if needs_segmentation:
                detected_lines, sections = enhanced_image_segmentation(
                    str(temp_image_path),
                    confidence_threshold=self.confidence_threshold,
                    min_line_distance=self.min_line_distance,
                )

                result["segmentation_performed"] = True
                result["detected_lines"] = detected_lines
                result["num_sections"] = len(sections)

                split_files = split_image_into_sections(
                    str(temp_image_path), sections, str(images_dir)
                )

                sections_info = []
                for i, (y_min, y_max) in enumerate(sections):
                    sections_info.append(
                        {
                            "index": i,
                            "y_min": y_min,
                            "y_max": y_max,
                            "height": y_max - y_min,
                            "file_path": split_files[i],
                        }
                    )

                result["segments"] = sections_info

                if sections_info:
                    result["image_path"] = sections_info[0]["file_path"]
                else:
                    final_image_path = images_dir / file_name
                    import shutil

                    shutil.copy2(temp_image_path, final_image_path)
                    result["image_path"] = str(final_image_path)
            else:
                final_image_path = images_dir / file_name
                import shutil

                shutil.copy2(temp_image_path, final_image_path)
                result["image_path"] = str(final_image_path)

            if temp_image_path.exists():
                temp_image_path.unlink()

            return result
        except Exception as e:
            tb = traceback.format_exc()
            if "temp_image_path" in locals() and temp_image_path.exists():
                temp_image_path.unlink()
            error_message = str(e)
            await self.error_repo.insert_error(
                Error(
                    user_id=request_context.get(),
                    error_message=f"[ERROR] occurred while processing image segmentation: {error_message} \nTraceback: {tb} \nError from image segmentation usecase in execute()",
                )
            )
            raise JsonResponseError(
                status_code=500, detail=f"Failed to process image: {error_message}",
                original_exception=e
            ) from e
