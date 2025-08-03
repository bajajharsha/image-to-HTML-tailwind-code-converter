from io import BytesIO

from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, File, UploadFile, Form
from fastapi import APIRouter, Depends, File, UploadFile, status

from backend.app.utils.error_handler import error_handler
from backend.app.models.schemas.image import ConversionResponse
from backend.app.controllers.convert_controller import ConvertController

router = APIRouter()


@router.post("/convert", response_model = ConversionResponse, status_code = status.HTTP_200_OK)
@error_handler
async def convert(
    image: UploadFile = File(...),
    use_heuristic: bool = Form(...),
    convert_controller: ConvertController = Depends()
):
    result = await convert_controller.convert_image(image=image, use_heuristic=use_heuristic)
    
    return ConversionResponse(
        message = "successfully generated code for your webpage image.",
        code = result["code"],
        request_id = result["request_id"]
    )
    
@router.post("/convert/stream")
@error_handler
async def convert_stream(
    image: UploadFile = File(...), 
    use_heuristic: bool = Form(...),
    convert_controller: ConvertController = Depends()
):
    contents = await image.read()
    
    buffer = BytesIO(contents)
    
    file_copy = UploadFile(
        filename = image.filename,
        file = buffer
    )
        
    async def stream_generator():
        try:
            yield f"data: [STARTING CODE GENERATION]\n\n"
            async for chunk in convert_controller.convert_image_stream(image=file_copy, use_heuristic = use_heuristic):
                yield f"data: {chunk}\n\n"
                
            yield f"data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            
    response = StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )
    
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "close"
    
    return response