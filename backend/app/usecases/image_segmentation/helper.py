# src/app/usecases/image_segmentation/helper.py
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from Web_page_Screenshot_Segmentation.blank_spliter import find_height_spliter
from Web_page_Screenshot_Segmentation.color_spliter import color_height_spliter


def separation_line_detection(
    img_path,
    var_thr=100,
    diff_thr=30,
    portion_thr=0.5,
    window_size=10,
    min_line_distance=100,
):
    """
    Detect horizontal separation lines in an image with strict minimum distance enforcement.

    :param img_path: Path to the input image
    :param var_thr: Variance threshold for blank space detection
    :param diff_thr: Difference threshold for border detection
    :param portion_thr: Portion threshold for border detection
    :param window_size: Size of the window to examine for variance
    :param min_line_distance: Minimum distance between detected lines (0 for auto-calculation)
    
    :return: List of row positions where separation lines were detected
    """
    # Load and convert image to grayscale if it's not already
    img = np.array(Image.open(img_path).convert("L"))
    img_height = img.shape[0]

    # Set min_line_distance based on image height if not specified
    if min_line_distance <= 0:
        min_line_distance = int(img_height * 0.03)  # Default to 3% of image height
        print(f"Using min_line_distance = {min_line_distance}px (3% of image height)")

    # Store initial candidate lines with their confidence scores
    candidate_lines = []

    # Iterate through the image rows
    for i in range(window_size + 1, len(img) - window_size - 1):
        upper = img[i - window_size - 1]
        window = img[i - window_size : i]
        lower = img[i]

        # Calculate variance of window
        var = np.var(window)

        # Check if window is blank (low variance)
        is_blank = var < var_thr

        # Check for border at top of window
        diff_top = np.abs(upper - window[0])
        is_border_top = (
            np.mean(diff_top) > diff_thr and np.mean(diff_top > diff_thr) > portion_thr
        )

        # Check for border at bottom of window
        diff_bottom = np.abs(lower - window[-1])
        is_border_bottom = (
            np.mean(diff_bottom) > diff_thr
            and np.mean(diff_bottom > diff_thr) > portion_thr
        )

        # If conditions met, add a separation line
        if is_blank and (is_border_top or is_border_bottom):
            if is_border_bottom:
                pos = i
            else:
                pos = i - window_size

            # Calculate confidence metric (higher means more likely to be a real separation)
            confidence = max(np.mean(diff_top), np.mean(diff_bottom))

            # Additional confidence boost for lines near the top or bottom of image sections
            # This helps prioritize lines that are actual section boundaries
            edge_proximity = min(pos, img_height - pos) / img_height
            if (
                edge_proximity < 0.05
            ):  # If line is within 5% of image height from top/bottom
                confidence *= 1.5

            candidate_lines.append((pos, confidence))

    # No lines detected
    if not candidate_lines:
        return []

    # Sort candidate lines by confidence (highest first)
    candidate_lines.sort(key=lambda x: x[1], reverse=True)

    # Apply greedy algorithm to select lines with minimum distance constraint
    selected_lines = []

    for pos, conf in candidate_lines:
        # Check if this line is far enough from all previously selected lines
        if all(
            abs(pos - existing_pos) >= min_line_distance
            for existing_pos in selected_lines
        ):
            selected_lines.append(pos)

    # Sort the selected lines by position (top to bottom)
    selected_lines.sort()

    # Ensure we keep the important structural lines (top, middle, bottom sections)
    if len(selected_lines) >= 3:
        final_lines = selected_lines
    else:
        # If we have too few lines, try a more adaptive approach
        # Reset and use a different strategy
        selected_lines = []

        # Always include the highest confidence line
        top_line = candidate_lines[0][0]
        selected_lines.append(top_line)

        # Try with a smaller minimum distance
        adaptive_min_distance = min_line_distance // 2

        for pos, conf in candidate_lines[1:]:
            if all(
                abs(pos - existing_pos) >= adaptive_min_distance
                for existing_pos in selected_lines
            ):
                selected_lines.append(pos)

        # Sort the selected lines by position
        final_lines = sorted(selected_lines)

    return final_lines

def enhanced_image_segmentation(
    image_path,
    confidence_threshold=0.6,
    min_line_distance=0,
    blank_var_thr=80,
    blank_diff_thr=40,
    blank_portion_thr=0.5,
    color_var_thr=100,
    color_diff_thr=15,
    window_size=10,
):
    """
    Enhanced semantic image segmentation combining multiple approaches

    :param image_path: Path to the input image
    :param confidence_threshold: Minimum confidence for a line to be considered valid
    :param min_line_distance: Minimum distance between detected lines (0 for auto-calculation)
    :param blank_var_thr: Variance threshold for blank space detection
    :param blank_diff_thr: Difference threshold for border detection
    :param blank_portion_thr: Portion threshold for border detection
    :param color_var_thr: Variance threshold for color detection
    :param color_diff_thr: Difference threshold for color detection
    :param window_size: Size of the window to examine for variance
    
    :return: List of detected line positions and their corresponding segments
    """
    # Load image in both PIL and OpenCV formats
    pil_img = Image.open(image_path).convert("RGB")
    img_height = pil_img.height
    img_cv = cv2.imread(image_path)

    # Auto-calculate minimum line distance if not specified
    if min_line_distance <= 0:
        min_line_distance = int(img_height * 0.05)  # 5% of height
        print(f"Using min_line_distance = {min_line_distance}px (5% of image height)")

    # ---- STAGE 1: Use both detection methods ----

    # Method 1: Using separation_line_detection
    lines_1 = separation_line_detection(
        image_path,
        var_thr=blank_var_thr,
        diff_thr=blank_diff_thr,
        portion_thr=blank_portion_thr,
        window_size=window_size,
        min_line_distance=min_line_distance,
    )

    # We need to generate confidence scores for these lines
    # For now, assign high confidence (0.8) to all lines from method 1
    candidate_lines_1 = [(line, 0.8) for line in lines_1]

    # Method 2: Using Web_page_Screenshot_Segmentation approaches
    blank_regions = find_height_spliter(img_cv, 102, 0.5)
    color_regions = color_height_spliter(img_cv, color_var_thr, color_diff_thr)

    # ---- STAGE 2: Combine and assign confidence scores ----
    all_candidates = []

    # Add lines from method 1 with their original confidence
    all_candidates.extend(candidate_lines_1)

    # Assign confidence to method 2 lines
    for line in blank_regions:
        # Check if this is already detected by method 1
        is_duplicate = any(
            abs(line - existing) < min_line_distance / 2 for existing in lines_1
        )
        # Higher confidence if confirmed by both methods
        confidence = 0.9 if is_duplicate else 0.7
        all_candidates.append((line, confidence))

    for line in color_regions:
        # Check if this color transition is near any previously detected line
        is_duplicate = any(
            abs(line - existing) < min_line_distance / 2 for existing in lines_1
        )
        is_near_blank = any(
            abs(line - blank) < min_line_distance / 2 for blank in blank_regions
        )

        # Assign confidence based on corroboration
        if is_duplicate:
            confidence = 0.9  # Highest if detected by multiple methods
        elif is_near_blank:
            confidence = 0.75  # High if near a blank region
        else:
            confidence = 0.6  # Lower if only detected by color method

        all_candidates.append((line, confidence))

    # ---- STAGE 3: Filter by confidence and minimum distance ----
    # Sort by confidence (highest first)
    all_candidates.sort(key=lambda x: x[1], reverse=True)

    # Apply greedy selection with minimum distance enforcement
    selected_lines = []

    for pos, conf in all_candidates:
        # Only consider lines with confidence above threshold
        if conf < confidence_threshold:
            continue

        # Enforce minimum distance
        if all(
            abs(pos - existing_pos) >= min_line_distance
            for existing_pos in selected_lines
        ):
            selected_lines.append(pos)

    # Sort by position (top to bottom)
    selected_lines.sort()

    # Create segments from selected lines
    segments = get_content_sections(image_path, selected_lines)

    return selected_lines, segments


def get_content_sections(img_path, lines):
    """
    Get content sections defined by the separation lines

    :param img_path: Path to the input image
    :param lines: List of line positions detected
    
    :return: List of tuples representing sections (y_min, y_max)
    """
    img = Image.open(img_path)
    img_height = img.height

    # Add top and bottom of image as boundaries
    all_boundaries = [0] + lines + [img_height]

    # Create sections from adjacent boundaries
    sections = [
        (all_boundaries[i], all_boundaries[i + 1])
        for i in range(len(all_boundaries) - 1)
    ]

    return sections


def visualize_enhanced_segmentation(img_path, lines, output_path=None):
    """
    Visualize detected separation lines with color coding based on the detection method

    :param img_path: Path to the input image
    :param lines: List of line positions detected
    :param output_path: Path to save the output image (if None, display it)
    
    :return: None
    """

    # Load image
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)

    # Try to load a font for labeling
    try:
        font = ImageFont.truetype("Arial", 16)
    except IOError:
        font = ImageFont.load_default()

    # Draw lines and labels with magenta color (different from both methods)
    for i, line_pos in enumerate(lines):
        # Draw a magenta line with increased thickness (6 pixels instead of 3)
        draw.line([(0, line_pos), (img.width, line_pos)], fill="magenta", width=6)

        # Add a label with the line number - increase font size too
        try:
            label_font = ImageFont.truetype("Arial", 20)  # Larger font
        except IOError:
            label_font = font

        draw.text((10, line_pos - 25), f"Line {i + 1}", fill="magenta", font=label_font)

    # Save or display the result
    if output_path:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        img = img.convert("RGB")
        img.save(output_path)
        print(f"Image with {len(lines)} separation lines saved to {output_path}")
    else:
        img.show()


def split_image_into_sections(img_path, sections, output_dir):
    """
    Split the image into separate files based on detected sections

    :param img_path: Path to the input image
    :param sections: List of tuples representing sections (y_min, y_max)
    :param output_dir: Directory to save the split images
    
    :return: List of output file paths
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the original image
    img = Image.open(img_path)

    # Create a file for each section
    output_files = []

    for i, (y_min, y_max) in enumerate(sections):
        # Crop the section
        section_img = img.crop((0, y_min, img.width, y_max))

        # Create filename
        base_name = os.path.basename(img_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = os.path.join(
            output_dir, f"{name_without_ext}_section_{i + 1}.png"
        )

        # Save the section
        section_img.save(output_file)
        output_files.append(output_file)

        print(f"Saved section {i + 1} to {output_file}")

    return output_files
