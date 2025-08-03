import re
import os
import json
import aiofiles
import traceback

from PIL import Image, ImageDraw, ImageFont

from fastapi import Depends

from backend.app.models.domain.error import Error
from backend.app.utils.error_handler import JsonResponseError
from backend.app.utils.context_util import request_context
from backend.app.repositories.error_repository import ErrorRepo
from backend.app.services.gemini_service import GeminiAPIService
from backend.app.prompts.bbox import BBOX_PROMPT, HEURISTIC_BBOX_PROMPT


class BboxHelper:
    def __init__(
        self,
        gemini_service: GeminiAPIService = Depends(),
        error_repo: ErrorRepo = Depends(),
    ):
        self.gemini_service = gemini_service
        self.error_repo = error_repo
        self.request_id = request_context.get()

    async def generate_bounding_boxes(self, img_path, use_heuristic: bool = False):
        """
        Generates bounding boxes for the given image using the Gemini API.
        
        :param img_path: Path to the image file.
        :param use_heuristic: Flag to indicate whether to use heuristic method.
        
        :return: List of bounding boxes with labels.
        """
        try:
    
            bbox_prompt = HEURISTIC_BBOX_PROMPT if use_heuristic else BBOX_PROMPT
            response_text = await self.gemini_service.generate_content_with_image(bbox_prompt,img_path)

            return response_text
        
        except FileNotFoundError:
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occured while processing bounding box : File not found \n error from bbox generation helper in generate_bounding_boxes()",
                )
            )
            raise JsonResponseError(
                status_code=404,
                detail=f"Image file not found: {img_path}"
            )
            
        except Exception as e:
            tb = traceback.format_exc()
            await self.error_repo.insert_error(
                Error(
                    user_id=self.request_id,
                    error_message=f"[ERROR] occured while processing bounding box : {str(e)} \nTraceback: {tb} \nerror from bbox generation helper in generate_bounding_boxes()",
                )
            )
            raise JsonResponseError(
                status_code=500,
                detail=f"Error processing Gemini API request: {str(e)}"
            )    

    async def draw_bboxes(self, img_path, labels, is_heuristic):
        """
        Draws bounding boxes on the image based on the provided labels.
        
        :param img_path: Path to the image file.
        :param labels: List of labels with bounding box coordinates.
        :param is_heuristic: Flag to indicate whether the labels are from heuristic method.
        
        :return: Image with drawn bounding boxes.
        """
        COLORS = {
            "header": "#FF0000",
            "logo": "#00FFFF",
            "nav_link": "#0000FF",
            "main_content_area": "#FF0000",
            "news_article": "#FF00FF",
            "text_block": "#FF0000",
            "headline": "#FF0000",
            "image": "#00FFFF",
            "link": "#0000FF",
            "icon": "#00FFFF",
            "sidebar": "#FFA500",
            "default":  "#FFA500" 
        }

        img = Image.open(img_path)
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size

        try:
            font = ImageFont.truetype("Arial", 20)
        except:
            font = ImageFont.load_default()

        for label in labels:
            if is_heuristic:
                bbox = label["bbox"]
                y_min, x_min, y_max, x_max = bbox
            else:
                bbox = [val * 10 for val in label["box_percent"]]
                x_min, y_min, x_max, y_max = bbox
            label_name = label["label"]

            x1 = int(x_min * img_width / 1000)
            y1 = int(y_min * img_height / 1000)
            x2 = int(x_max * img_width / 1000)
            y2 = int(y_max * img_height / 1000)

            x1, x2 = max(0, min(x1, img_width)), max(0, min(x2, img_width))
            y1, y2 = max(0, min(y1, img_height)), max(0, min(y2, img_height))

            color = COLORS.get(label_name.lower(), COLORS["default"])
            
            draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=3)
            
            text_position = (x1, y1 - 25)
        
            draw.text((text_position[0]-1, text_position[1]), label_name, fill="black", font=font)
            draw.text((text_position[0]+1, text_position[1]), label_name, fill="black", font=font)
            draw.text((text_position[0], text_position[1]-1), label_name, fill="black", font=font)
            draw.text((text_position[0], text_position[1]+1), label_name, fill="black", font=font)
    
            draw.text(text_position, label_name, fill=color, font=font)

        return img

    async def parse_gemini_response(self,response_text):
        """
        Parses the JSON response from Gemini to extract bounding boxes.
        
        :param response_text: The JSON response text from Gemini.
        
        :return: List of bounding boxes with labels.
        """
        if not response_text:
            return []

        cleaned_text = response_text.strip()
        if "```json" in cleaned_text:
            start = cleaned_text.find("```json") + 7
            end = cleaned_text.rfind("```")
            cleaned_text = cleaned_text[start:end].strip()
        elif "```" in cleaned_text:
            start = cleaned_text.find("```") + 3
            end = cleaned_text.rfind("```")
            cleaned_text = cleaned_text[start:end].strip()

        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            print(f"First parse attempt failed: {str(e)}")
            try:
                cleaned_text = cleaned_text.replace(",\n]", "\n]").replace(",]", "]")
                
                cleaned_text = re.sub(r'(\d+),(\d+)', r'\1.\2', cleaned_text)
                
                data = json.loads(cleaned_text)
                print("Successfully parsed JSON after cleanup")
                
            except json.JSONDecodeError as e2:
                try:
                    pattern = r'{\s*"label":\s*"[^"]+",\s*"(box_percent|box_2d)":\s*\[[^\]]+\]\s*}'
                    matches = re.findall(pattern, cleaned_text)
                    if matches:
                        fixed_json = "[" + ",".join(matches) + "]"
                        data = json.loads(fixed_json)
                        print(f"Extracted {len(data)} components with regex pattern")
                    else:
                        print("No valid components could be extracted with regex")
                        return []
                    
                except Exception as e3:
                    tb = traceback.format_exc()
                    await self.error_repo.insert_error(
                        Error(
                            user_id=self.request_id,
                            error_message=f"[ERROR] occured while processing bounding box : {str(e3)} \nTraceback: {tb}\nError from bbox generation helper in parse_gemini_response()",
                        )
                    )
                    print(f"All JSON parsing attempts failed: {str(e3)}")
                    print("Response text:", response_text)
                    return []
        
        standardized_data = []
        for item in data:
            if not isinstance(item, dict) or 'label' not in item:
                continue
                
            if 'box_2d' in item and len(item['box_2d']) == 4:
                y_min, x_min, y_max, x_max = item['box_2d']
                standardized_data.append({
                    'label': item['label'],
                    'box_percent': [x_min/10, y_min/10, x_max/10, y_max/10]
                })
            elif 'box_percent' in item and len(item['box_percent']) == 4:
                standardized_data.append(item)
        
        print(f"Successfully processed {len(standardized_data)} components.")
        return standardized_data
    
    async def parse_gemini_response_for_heuristic(self, response_text):
        """
        Parses the JSON response from Gemini to extract bounding boxes using heuristic method.
        
        :param response_text: The JSON response text from Gemini.
        
        :return: List of bounding boxes with labels.
        """
        if not response_text:
            return []

        cleaned_text = response_text.strip()
        if "```json" in cleaned_text:
    
            start = cleaned_text.find("```json") + 7
            end = cleaned_text.rfind("```")
            cleaned_text = cleaned_text[start:end].strip()
            
        elif "```" in cleaned_text:

            start = cleaned_text.find("```") + 3
            end = cleaned_text.rfind("```")
            cleaned_text = cleaned_text[start:end].strip()

        try:
            data = json.loads(cleaned_text)
            
        except json.JSONDecodeError as e:
            print(f"First parse attempt failed: {str(e)}")
            try:
                cleaned_text = cleaned_text.replace(",\n]", "\n]").replace(",]", "]")
            
                import re
                cleaned_text = re.sub(r'(\d+),(\d+)', r'\1.\2', cleaned_text)
                
                data = json.loads(cleaned_text)
                print("Successfully parsed JSON after cleanup")
                
            except json.JSONDecodeError as e2:
                try:
                    
                    import re
                
                    pattern = r'{\s*"bbox":\s*\[[^\]]+\],\s*"label":\s*"[^"]+",\s*"description":\s*"[^"]*"'
                    matches = re.findall(pattern, cleaned_text)
                    if matches:
        
                        fixed_json = "[" + ",".join([match + "}" for match in matches]) + "]"
                        data = json.loads(fixed_json)
                        print(f"Extracted {len(data)} components with regex pattern")
                    else:
                        print("No valid components could be extracted with regex")
                        return []
                    
                except Exception as e3:
                    print(f"All JSON parsing attempts failed: {str(e3)}")
                    print("Response text:", response_text)
                    return []
        
        print(f"Successfully processed {len(data)} components.")
        return data


    def filter_nested_elements(self,components):
        """
        Filters out nested elements from the list of components based on their labels.
        
        :param components: List of components with labels and bounding boxes.
        
        :return: Filtered list of components without nested elements.
        """
        parent_elements = ['div', 'header', 'footer', 'sidebar', 'navbar', 'search-bar', 'form']
        
        filtered_components = []
        
        parent_boxes = []
        for component in components:
            label = component['label'].lower()
            if any(label == parent or label.startswith(parent + '_') for parent in parent_elements):
                parent_boxes.append(component)
        
        for component in components:
            label = component['label'].lower()
            box = component['box_percent']
            
            if 'image' in label:
                filtered_components.append(component)
                continue
            
            should_keep = True
            
            for parent in parent_boxes:
                if component == parent:
                    continue
                    
                parent_box = parent['box_percent']
                
                
                margin = 0.5
                if (box[0] >= parent_box[0] - margin and box[2] <= parent_box[2] + margin and
                    box[1] >= parent_box[1] - margin and box[3] <= parent_box[3] + margin and
                
                    (box[0] != parent_box[0] or box[1] != parent_box[1] or box[2] != parent_box[2] or box[3] != parent_box[3])):
                    
                
                    print(f"Filtering out nested {label} inside {parent['label']}")
                    should_keep = False
                    break
                    
            if should_keep:
                filtered_components.append(component)
        
        print(f"Filtered out {len(components) - len(filtered_components)} nested elements")
        return filtered_components


    async def save_components_to_json(self,components, output_path):
        """
        Save the component data to a JSON file asynchronously.
        
        :param components: List of components with labels and bounding boxes.
        :param output_path: Path to save the JSON file.
        
        :return: True if saved successfully, False otherwise.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            json_data = []
            for comp in components:
               
                x_min, y_min, x_max, y_max = comp['box_percent']
                json_data.append({
                    "label": comp['label'],
                    "box_2d": [int(y_min * 10), int(x_min * 10), int(y_max * 10), int(x_max * 10)]
                })
            
            async with aiofiles.open(output_path, 'w') as f:
                json_string = json.dumps(json_data, indent=2)
                await f.write(json_string)
                
            print(f"Saved JSON data to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving JSON file: {str(e)}")
            try:
                with open(output_path, 'w') as f:
                    json.dump(json_data, f, indent=2)
                print(f"Saved JSON data using fallback method")
                return True
            
            except Exception as e2:
                await self.error_repo.insert_error(
                    Error(
                        user_id=self.request_id,
                        error_message=f"[ERROR] occured while processing bounding box : {str(e2)} \n error from bbox generation helper in save_components_to_json()",
                    )
                )
                print(f"Fallback also failed: {str(e2)}")
                return False
            
    async def save_components_to_json_heu(self, components, output_path):
        """
        Save the component data to a JSON file asynchronously using heuristic method.
        
        :param components: List of components with labels and bounding boxes.
        :param output_path: Path to save the JSON file.
        
        :return: True if saved successfully, False otherwise.
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            async with aiofiles.open(output_path, 'w') as f:
                json_string = json.dumps(components, indent=2)
                await f.write(json_string)
                
            print(f"Saved JSON data to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving JSON file: {str(e)}")
            try:
                with open(output_path, 'w') as f:
                    json.dump(components, f, indent=2)
                print(f"Saved JSON data using fallback method")
                return True
            
            except Exception as e2:
                print(f"Fallback also failed: {str(e2)}")
                return False


