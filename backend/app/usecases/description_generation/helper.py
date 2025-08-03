import os
import json
import uuid
import numpy as np
import tempfile
import traceback
from PIL import Image, ImageDraw
from typing import Dict, Any, List, Optional
from backend.app.services.claude_service import ClaudeService
from fastapi import Depends
from backend.app.models.domain.error import Error
from backend.app.repositories.error_repository import ErrorRepo
from backend.app.utils.context_util import request_context
from colorthief import ColorThief

try:
    COLOR_THIEF_AVAILABLE = True
except ImportError:
    COLOR_THIEF_AVAILABLE = False
    print("ColorThief not available. Installing or using fallback...")

class DescriptionHelper:
    def __init__(self, claude_service: ClaudeService = Depends(), error_repo: ErrorRepo = Depends()):
        self.claude_service = claude_service
        self.request_id = None 
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_tokens = 0
        self.error_repo = error_repo

    def clip_and_save_image(self, img_path: str, box_2d: List[float], component_id: str, output_dir: str) -> str:
        """
        Clips an image component from the original image and saves it.
        
        :param img_path: Path to the original image.
        :param box_2d: List of coordinates [y_min, x_min, y_max, x_max] for the component.
        :param component_id: Unique identifier for the component.
        :param output_dir: Directory to save the cropped image.
        
        :return: Path to the saved cropped image.
        
        """
        img = Image.open(img_path).convert("RGB")
        img_width, img_height = img.size
        
        y_min, x_min, y_max, x_max = box_2d
        x1 = int(x_min * img_width / 1000)
        y1 = int(y_min * img_height / 1000)
        x2 = int(x_max * img_width / 1000)
        y2 = int(y_max * img_height / 1000)
        
        x1, x2 = max(0, min(x1, img_width)), max(0, min(x2, img_width))
        y1, y2 = max(0, min(y1, img_height)), max(0, min(y2, img_height))
        
        cropped_img = img.crop((x1, y1, x2, y2))
        
        assets_dir = os.path.join("uploads", self.request_id, "final", "assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        img_ext = os.path.splitext(img_path)[1]
        if not img_ext:
            img_ext = ".jpg" 
        img_filename = f"image_{component_id}{img_ext}"
        img_save_path = os.path.join(assets_dir, img_filename)
        
        if img_ext.lower() in ['.jpg', '.jpeg']:
            cropped_img = cropped_img.convert('RGB')
        cropped_img.save(img_save_path)
        
        return os.path.join("assets", img_filename)
    
    def highlight_component(self, img_path: str, box_2d: List[float], temp_output_path: str) -> str:
        """
        Creates a version of the image with a single component highlighted.
        
        :param img_path: Path to the original image.
        :param box_2d: List of coordinates [y_min, x_min, y_max, x_max] for the component.
        :param temp_output_path: Path to save the highlighted image.
        
        :return: Path to the saved highlighted image.

        """
        img = Image.open(img_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        img_width, img_height = img.size
        
        y_min, x_min, y_max, x_max = box_2d
        x1 = int(x_min * img_width / 1000)
        y1 = int(y_min * img_height / 1000)
        x2 = int(x_max * img_width / 1000)
        y2 = int(y_max * img_height / 1000)
        
        x1, x2 = max(0, min(x1, img_width)), max(0, min(x2, img_width))
        y1, y2 = max(0, min(y1, img_height)), max(0, min(y2, img_height))
        
        draw.rectangle([(x1, y1), (x2, y2)], outline="#FF0000", width=5)
        
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        overlay_draw.rectangle([(0, 0), (img_width, img_height)], fill=(0, 0, 0, 80))
        overlay_draw.rectangle([(x1, y1), (x2, y2)], fill=(0, 0, 0, 0))
        
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        
        img.save(temp_output_path)
        return temp_output_path

    async def analyze_component_with_claude_async(self, img_path: str, component_label: str, component_id: str) -> Dict[str, Any]:
        """
        Asynchronously analyzes a single UI component using the Claude API with streaming.
        
        :param img_path: Path to the original image.
        :param component_label: Label of the component to analyze.
        :param component_id: Unique identifier for the component.
        
        :return: A dictionary containing the analyzed component's details.
        
        """
        
        try:
            from backend.app.prompts.description_generation import user_prompt, system_prompt
            
            prompt = user_prompt.format(
                component_label=component_label
            )

            sys_prompt = system_prompt.format(component_label=component_label)

            response_data = await self.claude_service.generate_content(prompt, img_path, sys_prompt)
            
            usage = response_data["usage"]
            input_tokens = usage["input_tokens"]
            output_tokens = usage["output_tokens"]
            
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_tokens += input_tokens + output_tokens
            
            print(f"  [{component_id}] Token usage: {input_tokens} input, {output_tokens} output, {input_tokens + output_tokens} total")

            response_text = response_data["content"][0]["text"]
            
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
                component_data = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Problematic JSON string: {cleaned_text[:100]}...")  # Print beginning of string
                
                await self.error_repo.insert_error(
                    Error(
                        user_id=request_context.get(),
                        error_message=f"[ERROR] JSON parsing error: {str(e)}\nJSON string: {cleaned_text[:200]}\n\nError from description_helper in analyze_component_with_claude_async()",
                    )
                )
                
                return {
                    "type": component_label,
                    "styles": {
                        "colorPalette": {},
                        "typography": {},
                        "spacing": {"padding": {}, "margin": {}},
                        "layout": {}
                    },
                    "content": {},
                    "media": {"images": [], "icons": []},
                    "children": []
                }
            
            print(f"✓ [{component_id}] Analysis complete for {component_label}")
            return component_data
            
        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error analyzing component {component_id}: {str(e)}")
            await self.error_repo.insert_error(
                Error(
                    user_id=request_context.get(),
                    error_message=f"[ERROR] occurred while processing component analysis: {str(e)} \nTraceback: {tb} \nError from description_helper in analyze_component_with_claude_async()",
                )
            )
            return {
                "type": component_label,
                "styles": {
                    "colorPalette": {},
                    "typography": {},
                    "spacing": {"padding": {}, "margin": {}},
                    "layout": {}
                },
                "content": {},
                "media": {"images": [], "icons": []},
                "children": []
            }
        
    def _is_contained_within(self, child_box: List[float], parent_box: List[float]) -> bool:
        """
        Check if a box is contained within another box.
        
        :param child_box: List of coordinates [y_min, x_min, y_max, x_max] for the child box.
        :param parent_box: List of coordinates [y_min, x_min, y_max, x_max] for the parent box.
        
        :return: True if the child box is contained within the parent box, False otherwise.
        """
        margin = 5 
        
        child_y_min, child_x_min, child_y_max, child_x_max = child_box
        parent_y_min, parent_x_min, parent_y_max, parent_x_max = parent_box
        
        return (parent_y_min - margin <= child_y_min and 
                parent_x_min - margin <= child_x_min and 
                parent_y_max + margin >= child_y_max and 
                parent_x_max + margin >= child_x_max)

    def _find_parent_index(self, element_index: int, elements: List[Dict[str, Any]]) -> Optional[int]:
        """
        Find the index of the parent element for a given element.
        
        :param element_index: Index of the element to find the parent for.
        :param elements: List of all elements in the UI structure.
        
        :return: Index of the parent element, or None if no parent is found.
        
        """
        element = elements[element_index]
        element_box = element["bbox"]
        
        potential_parents = []
        for i, other in enumerate(elements):
            if i == element_index:
                continue
                
            if self._is_contained_within(element_box, other["bbox"]):
                potential_parents.append((i, other))
        
        if not potential_parents:
            return None
        
        def calculate_area(box):
            return (box[2] - box[0]) * (box[3] - box[1])
        
        smallest_parent = min(potential_parents, 
                            key=lambda parent: calculate_area(parent[1]["bbox"]))
        
        return smallest_parent[0]
        
    def convert_json_structure(self, input_json: List[Dict[str, Any]], image_path: str = None) -> Dict[str, Any]:
        """
        Convert flat JSON structure to hierarchical structure.
        
        :param input_json: List of dictionaries representing the UI components.
        :param image_path: Path to the original image (optional).
        
        :return: Dictionary representing the hierarchical structure of components.
        
        """
        # Create output directory if it doesn't exist
        # if image_path and output_dir:
        #     os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Create unique IDs for each component
        components = []
        for i, element in enumerate(input_json):
            comp_id = f"comp_{i+1}"
            components.append({
                "id": comp_id,
                "original_data": element,
                "children_indices": [],
                "media_indices": [],
                "parent_index": None
            })
        
        # Step 2: Identify parent-child relationships and media elements
        media_elements = []
        
        for i, component in enumerate(components):
            element = component["original_data"]
            
            if element["label"].lower() in ["image", "logo", "icon"]:
                media_elements.append(i)
            
            parent_index = self._find_parent_index(i, [comp["original_data"] for comp in components])
            if parent_index is not None:
                component["parent_index"] = parent_index
                components[parent_index]["children_indices"].append(i)
        
        # Step 3: Process media elements - determine if they belong to any parent
        tracking_container = []
        media_tracking_map = {} 
        
        if image_path:
            try:
                img = Image.open(image_path)
                img_width, img_height = img.size
                
                for media_index in media_elements:
                    media = components[media_index]
                    media_box = media["original_data"]["bbox"]
                    
                    y_min, x_min, y_max, x_max = media_box
                    
                    x_min_px = int(x_min * img_width / 1000)
                    y_min_px = int(y_min * img_height / 1000)
                    x_max_px = int(x_max * img_width / 1000)
                    y_max_px = int(y_max * img_height / 1000)
                    
                    x_min_px = max(0, min(x_min_px, img_width - 1))
                    y_min_px = max(0, min(y_min_px, img_height - 1))
                    x_max_px = max(0, min(x_max_px, img_width - 1))
                    y_max_px = max(0, min(y_max_px, img_height - 1))
                    
                    if x_min_px >= x_max_px or y_min_px >= y_max_px:
                        continue
                    
                    media_crop = img.crop((x_min_px, y_min_px, x_max_px, y_max_px))
                    
                    assets_dir = os.path.join("uploads", self.request_id, "final","assets")
                    os.makedirs(assets_dir,exist_ok=True)

                    component_id = str(uuid.uuid4())[:8]

                    img_ext = os.path.splitext(image_path)[1]
                    if not img_ext:
                        img_ext = ".jpg"
                    img_filename = f"image_{component_id}{img_ext}"
                    image_save_path = os.path.join(assets_dir, img_filename)
                    
                    web_file_path = f"assets/{img_filename}"
                    
                    if img_ext.lower() in ['.jpg', '.jpeg']:
                        media_crop = media_crop.convert('RGB')
                    media_crop.save(image_save_path)
                    
                    tracking_entry = {
                        "original_label": media["original_data"]["label"],
                        "coordinates": {
                            "y_min": y_min,
                            "x_min": x_min,
                            "y_max": y_max,
                            "x_max": x_max
                        },
                        "file_path": web_file_path,
                        "type": media["original_data"]["label"].lower()
                    }
                    
                    tracking_container.append(tracking_entry)
                    
                    media_tracking_map[media_index] = tracking_entry
                    
                    if media["parent_index"] is not None:
                        components[media["parent_index"]]["media_indices"].append(media_index)
                    
            except Exception as e:
                print(f"Error processing media elements: {str(e)}")
        else:
            for media_index in media_elements:
                media = components[media_index]
                media_box = media["original_data"]["bbox"]
                
                web_file_path = f"assets/image_{media_index}.png"
                
                tracking_entry = {
                    "original_label": media["original_data"]["label"],
                    "coordinates": {
                        "y_min": media_box[0],
                        "x_min": media_box[1],
                        "y_max": media_box[2],
                        "x_max": media_box[3]
                    },
                    "file_path": web_file_path,
                    "type": media["original_data"]["label"].lower()
                }
                
                tracking_container.append(tracking_entry)
                
                media_tracking_map[media_index] = tracking_entry
                
                if media["parent_index"] is not None:
                    components[media["parent_index"]]["media_indices"].append(media_index)
        
        # Step 4: Build the hierarchical structure
        result = {}
        
        def _build_component_structure(component_index: int) -> Dict[str, Any]:
            component = components[component_index]
            original = component["original_data"]
            box = original["bbox"]
            
            media_list = []
            
            if component_index in media_tracking_map:
                media_list.append(media_tracking_map[component_index])
                
            for media_idx in component["media_indices"]:
                if media_idx in media_tracking_map:
                    media_list.append(media_tracking_map[media_idx])
            
            children = []
            for child_idx in component["children_indices"]:
                if child_idx in component["media_indices"]:
                    continue
                    
                child_structure = _build_component_structure(child_idx)
                children.append(child_structure)
            
            return {
                "id": component["id"],
                "type": original["label"],
                "coordinates": {
                    "y1": int(box[0]),
                    "x1": int(box[1]),
                    "y2": int(box[2]),
                    "x2": int(box[3])
                },
                "description": {
                    "type": original["label"],
                    "description": original.get("description", ""),
                    "content": {
                        "text": original.get("text", ""),
                        "media": media_list
                    },
                    "children": children
                }
            }
        
        root_indices = [i for i, comp in enumerate(components) if comp["parent_index"] is None]
        
        for idx in root_indices:
            comp = components[idx]
            result[comp["id"]] = _build_component_structure(idx)
        
        return result
    
    
    def process_component_structure(self, input_json):
        """
        Process the component structure to add styles and layout fields to each component
        in the hierarchy.
        
        :param input_json: JSON data representing the component structure.
        
        :return: Processed JSON data with styles and layout fields added.
        
        """
        data = json.loads(input_json) if isinstance(input_json, str) else input_json
        
        viewport = {
            "y1": 0, 
            "x1": 0, 
            "y2": 1000, 
            "x2": 1000
        }
        
        component_map = {}
        
        for comp_id, component in data.items():
            component_map[comp_id] = component
        
        for comp_id, component in data.items():
            self._process_component(component, component_map, viewport)
            
            if "description" in component and "content" in component["description"] and "media" in component["description"]["content"]:
                for media in component["description"]["content"]["media"]:
                    self._process_media_element(media, component, viewport)
            
            if "description" in component and "children" in component["description"]:
                for child in component["description"]["children"]:
                    self._process_component(child, component_map, viewport, parent=component)
        
        return data

    def _process_component(self, component, component_map, viewport, parent=None):
        """
        Process a single component to add styles and layout fields.
        
        :param component: Component to process
        :param component_map: Map of all components
        :param viewport: Viewport dimensions
        :param parent: Parent component (if any)
        
        :return: None
        
        """
        if "description" not in component:
            return
        
        coords = component["coordinates"] if "coordinates" in component else {}
        
        width = coords.get("x2", 0) - coords.get("x1", 0)
        height = coords.get("y2", 0) - coords.get("y1", 0)
        
        if "styles" not in component["description"]:
            component["description"]["styles"] = {
                "width": str(width),
                "height": str(height),
                "colorPalette": []
            }
        
        parent_coords = parent["coordinates"] if parent else viewport
        
        parent_width = parent_coords.get("x2", 0) - parent_coords.get("x1", 0)
        parent_height = parent_coords.get("y2", 0) - parent_coords.get("y1", 0)
        
        top_percent = round((coords.get("y1", 0) - parent_coords.get("y1", 0)) / parent_height * 100, 2) if parent_height else 0
        left_percent = round((coords.get("x1", 0) - parent_coords.get("x1", 0)) / parent_width * 100, 2) if parent_width else 0
        right_percent = round((parent_coords.get("x2", 0) - coords.get("x2", 0)) / parent_width * 100, 2) if parent_width else 0
        bottom_percent = round((parent_coords.get("y2", 0) - coords.get("y2", 0)) / parent_height * 100, 2) if parent_height else 0
        
        body_top_percent = round(coords.get("y1", 0) / viewport.get("y2", 1000) * 100, 2)
        body_left_percent = round(coords.get("x1", 0) / viewport.get("x2", 1000) * 100, 2)
        body_right_percent = round((viewport.get("x2", 1000) - coords.get("x2", 0)) / viewport.get("x2", 1000) * 100, 2)
        body_bottom_percent = round((viewport.get("y2", 1000) - coords.get("y2", 0)) / viewport.get("y2", 1000) * 100, 2)
        
        width_percent = round(width / parent_width * 100, 2) if parent_width else 0
        height_percent = round(height / parent_height * 100, 2) if parent_height else 0
        
        tailwind_classes = []
        
        if parent:
            positioning = self._determine_positioning(component, parent)
            tailwind_classes.append(positioning)
        else:
            tailwind_classes.append("relative")
        
        tailwind_classes.append(f"w-[{width_percent}%]")
        tailwind_classes.append(f"h-[{height_percent}%]")
        
        if parent and "absolute" in tailwind_classes:
            if top_percent < bottom_percent:
                tailwind_classes.append(f"top-[{top_percent}%]")
            else:
                tailwind_classes.append(f"bottom-[{bottom_percent}%]")
                
            if left_percent < right_percent:
                tailwind_classes.append(f"left-[{left_percent}%]")
            else:
                tailwind_classes.append(f"right-[{right_percent}%]")
        
        component["description"]["layout"] = {
            "%_position_parent": {
                "top": str(top_percent),
                "right": str(right_percent),
                "bottom": str(bottom_percent),
                "left": str(left_percent)
            },
            "%_position_body": {
                "top": str(body_top_percent),
                "right": str(body_right_percent),
                "bottom": str(body_bottom_percent),
                "left": str(body_left_percent)
            },
            "tailwind_classes": " ".join(tailwind_classes)
        }

    def _process_media_element(self, media, parent_component, viewport):
        """
        Process a media element to add styles and layout fields.
        
        :param media: Media element to process
        :param parent_component: Parent component containing the media element
        :param viewport: Viewport dimensions
        
        :return: None
        
        """
        
        if "coordinates" not in media:
            return
            
        coords = {
            "y1": media["coordinates"]["y_min"],
            "x1": media["coordinates"]["x_min"],
            "y2": media["coordinates"]["y_max"],
            "x2": media["coordinates"]["x_max"]
        }
        
        width = coords["x2"] - coords["x1"]
        height = coords["y2"] - coords["y1"]
        
        if "styles" not in media:
            media["styles"] = {
                "width": str(width),
                "height": str(height),
                "colorPalette": []
            }
        
        parent_coords = parent_component["coordinates"]
        
        top_px = coords["y1"] - parent_coords["y1"]
        left_px = coords["x1"] - parent_coords["x1"]
        right_px = parent_coords["x2"] - coords["x2"]
        bottom_px = parent_coords["y2"] - coords["y2"]
        
        body_top_px = coords["y1"]
        body_left_px = coords["x1"]
        body_right_px = viewport["x2"] - coords["x2"]
        body_bottom_px = viewport["y2"] - coords["y2"]
        
        tailwind_classes = []
        
        tailwind_classes.append("absolute")
        
        tailwind_classes.append(f"w-[{width}px]")
        tailwind_classes.append(f"h-[{height}px]")
        
        tailwind_classes.append(f"top-[{top_px}px]")
        tailwind_classes.append(f"left-[{left_px}px]")
        
        media["layout"] = {
            "position_parent": {
                "top": str(top_px),
                "right": str(right_px),
                "bottom": str(bottom_px),
                "left": str(left_px)
            },
            "position_body": {
                "top": str(body_top_px),
                "right": str(body_right_px),
                "bottom": str(body_bottom_px),
                "left": str(body_left_px)
            },
            "tailwind_classes": " ".join(tailwind_classes)
        }

    def _determine_positioning(self, component, parent):
        """
        Determine the most appropriate positioning strategy for the component.
        
        :param component: Component to process
        :param parent: Parent component containing the component
        
        :return: Positioning strategy (e.g., "absolute", "relative")
        """
        
        component_type = component.get("type", "").lower()
        parent_type = parent.get("type", "").lower()
        
        has_overlap = self._has_overlap_with_siblings(component, parent)
        
        absolute_components = ["modal", "tooltip", "dropdown", "popup", "overlay", "dialog", "menu"]
        absolute_container_parents = ["card", "container", "section", "article", "main", "div", "header", "footer"]
        
        if has_overlap:
            return "absolute"
        
        if component_type in absolute_components:
            return "absolute"
        
        if parent_type in absolute_container_parents:
            if len(parent.get("description", {}).get("children", [])) <= 1:
                return "relative"
            
            return "absolute"
        
        return "relative"

    def _has_overlap_with_siblings(self, component, parent):
        """
        Check if the component overlaps with any of its siblings.
        
        :param component: Component to check for overlap
        :param parent: Parent component containing the component
        
        :return: True if there is an overlap, False otherwise
        """
        
        comp_coords = component.get("coordinates", {})
        if not comp_coords:
            return False
        
        comp_x1 = comp_coords.get("x1", 0)
        comp_y1 = comp_coords.get("y1", 0)
        comp_x2 = comp_coords.get("x2", 0)
        comp_y2 = comp_coords.get("y2", 0)
        
        siblings = []
        if "description" in parent and "children" in parent["description"]:
            siblings = parent["description"]["children"]
        
        for sibling in siblings:
            if sibling.get("id") == component.get("id") or "coordinates" not in sibling:
                continue
            
            sib_coords = sibling.get("coordinates", {})
            sib_x1 = sib_coords.get("x1", 0)
            sib_y1 = sib_coords.get("y1", 0)
            sib_x2 = sib_coords.get("x2", 0)
            sib_y2 = sib_coords.get("y2", 0)
            
            x_overlap = (comp_x1 < sib_x2) and (comp_x2 > sib_x1)
            y_overlap = (comp_y1 < sib_y2) and (comp_y2 > sib_y1)
            
            if x_overlap and y_overlap:
                return True
        
        return False
    
    def _create_medialess_image(self, image_path, json_data, output_path=None):
        """
        Create a copy of the original image with all media elements removed (filled with white).
        
        :param image_path: Path to the original image.
        :param json_data: JSON data containing the coordinates of media elements.
        :param output_path: Path to save the medialess image (optional).
        
        :return: PIL Image object of the medialess image.
        
        """

        img = Image.open(image_path).convert("RGB")
        img_width, img_height = img.size
        
        draw = ImageDraw.Draw(img)
        
        for comp_id, comp_data in json_data.items():
            if comp_data["type"] in ["media", "icon", "logo", "image"]:
                coords = comp_data["coordinates"]
                x1 = int(coords["x1"] * img_width / 1000)
                y1 = int(coords["y1"] * img_height / 1000)
                x2 = int(coords["x2"] * img_width / 1000)
                y2 = int(coords["y2"] * img_height / 1000)
                
                x1, x2 = max(0, min(x1, img_width)), max(0, min(x2, img_width))
                y1, y2 = max(0, min(y1, img_height)), max(0, min(y2, img_height))
                
                draw.rectangle([(x1, y1), (x2, y2)], fill="white")
            
            if "description" in comp_data and "content" in comp_data["description"]:
                if "media" in comp_data["description"]["content"] and comp_data["description"]["content"]["media"]:
                    for media_item in comp_data["description"]["content"]["media"]:
                        coords = media_item["coordinates"]
                        x1 = int(coords["x_min"] * img_width / 1000)
                        y1 = int(coords["y_min"] * img_height / 1000)
                        x2 = int(coords["x_max"] * img_width / 1000)
                        y2 = int(coords["y_max"] * img_height / 1000)
                        
                        x1, x2 = max(0, min(x1, img_width)), max(0, min(x2, img_width))
                        y1, y2 = max(0, min(y1, img_height)), max(0, min(y2, img_height))
                        
                        draw.rectangle([(x1, y1), (x2, y2)], fill="white")
        
        if output_path:
            file_ext = os.path.splitext(output_path)[1].lower()
            if file_ext in ['.jpg', '.jpeg']:
                img = img.convert('RGB')
            img.save(output_path)
        
        return img

    def _extract_dominant_colors(self, image, bbox, max_colors=5):
        """
        Extract dominant colors from a cropped region of an image.
        
        :param image: PIL Image object
        :param bbox: Bounding box coordinates (left, upper, right, lower)
        :param max_colors: Maximum number of colors to extract
        
        :return: List of hex color strings
        
        """
        
        cropped = image.crop(bbox)
        
        if COLOR_THIEF_AVAILABLE:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            try:
                cropped.save(temp_file.name)
                color_thief = ColorThief(temp_file.name)
                palette = color_thief.get_palette(color_count=max_colors)
                hex_palette = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
            except Exception as e:
                print(f"Error extracting colors: {str(e)}")
                hex_palette = self._fallback_extract_colors(cropped, max_colors)
            finally:
                temp_file.close()
                os.unlink(temp_file.name)
        else:
            hex_palette = self._fallback_extract_colors(cropped, max_colors)
        
        return hex_palette

    def _fallback_extract_colors(self, image, max_colors=5):
        """
        Fallback method to extract dominant colors using NumPy.
        
        :param image: PIL Image object
        :param max_colors: Maximum number of colors to extract
        
        :return: List of hex color strings
        
        """
        
        try:
            img_array = np.array(image)
            
            pixels = img_array.reshape(-1, 3)
            
            if pixels.shape[0] <= 1:
                return ["#ffffff"] 
            
            unique_colors = np.unique(pixels, axis=0)
            
            if len(unique_colors) > max_colors:
                step = len(unique_colors) // max_colors
                unique_colors = unique_colors[::step][:max_colors]
            
            hex_palette = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in unique_colors[:max_colors]]
            
            return hex_palette
        except Exception as e:
            print(f"Error in fallback color extraction: {str(e)}")
            return ["#ffffff"]      

    def _process_component_for_color(self, comp_data, medialess_img, img_width, img_height, processed=None):
        """
        Recursively process a component and its children to extract color palettes.
        
        :param comp_data: Component data to process
        :param medialess_img: Medialess image to analyze
        :param img_width: Width of the image
        :param img_height: Height of the image
        :param processed: Set of processed component IDs to avoid duplicates
        
        :return: Processed component data with color palettes
        
        """
        if processed is None:
            processed = set()
        
        if "id" in comp_data and comp_data["id"] in processed:
            return comp_data
        if comp_data.get("type") in ["media", "icon", "logo", "image"]:
            return comp_data
        
        if "id" in comp_data:
            processed.add(comp_data["id"])
        
        coords = comp_data.get("coordinates", {})
        if coords:
            x1 = int(coords.get("x1", 0) * img_width / 1000)
            y1 = int(coords.get("y1", 0) * img_height / 1000)
            x2 = int(coords.get("x2", 0) * img_width / 1000)
            y2 = int(coords.get("y2", 0) * img_height / 1000)
            
            x1, x2 = max(0, min(x1, img_width)), max(0, min(x2, img_width))
            y1, y2 = max(0, min(y1, img_height)), max(0, min(y2, img_height))
            
            if x2 > x1 and y2 > y1:
                color_palette = self._extract_dominant_colors(medialess_img, (x1, y1, x2, y2))
                
                if "description" in comp_data and "styles" in comp_data["description"]:
                    comp_data["description"]["styles"]["colorPalette"] = color_palette
        
        if "description" in comp_data and "children" in comp_data["description"]:
            for i, child in enumerate(comp_data["description"]["children"]):
                comp_data["description"]["children"][i] = self._process_component_for_color(
                    child, medialess_img, img_width, img_height, processed
                )
        
        return comp_data

    def extract_color_palettes(self, image_path, json_data, output_medialess_path=None):
        """
        Main function to process an image and its JSON description,
        extract color palettes for each element, and update the JSON.
        
        :param image_path: Path to the original image.
        :param json_data: JSON data containing the coordinates of media elements.
        :param output_medialess_path: Path to save the medialess image (optional).
        
        :return: Updated JSON data with color palettes.
        
        """
        
        if isinstance(json_data, str):
            with open(json_data, 'r') as f:
                json_data = json.load(f)
        
        medialess_img = self._create_medialess_image(image_path, json_data, output_medialess_path)
        img_width, img_height = medialess_img.size
        
        if output_medialess_path:
            print(f"Created medialess image at: {output_medialess_path}")
        
        processed = set()
        updated_json = {}
        for comp_id, comp_data in json_data.items():
            updated_json[comp_id] = self._process_component_for_color(
                comp_data, medialess_img, img_width, img_height, processed
            )
        
        return updated_json