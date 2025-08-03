HEURISTICS_GENERATE_CODE = f"""
    You are an expert HTML and Tailwind CSS developer specialized in converting images to pixel-perfect web interfaces.

    I've provided you with:
    1. An image of a website interface
    2. A detailed description of the interface that contains element hierarchy, bounding boxes, labels, descriptions,content, Tailwind CSS calsses

    Your task is to generate a pixel-perfect HTML and Tailwind CSS implementation of the provided website interface.

    ## ANALYSIS APPROACH (Before writing any code)
    1. First, analyze the entire component hierarchy to understand parent-child relationships
    2. Identify key layout patterns

    The JSON represents a very accurate hierarchical structure of the UI with:
    - type of each element.
    - coordinates of each element for your reference.
    - description that contains type, description, content, children, styles and layout.

    Keep track of the layout and styles information of each element that you encounter to help you generate a responsive HTML and Tailwind CSS implementation.

    ## HTML GENERATION GUIDELINES
    1. Create a semantically correct HTML structure
    2. Consider the layout and styles information of each element as the ground truth and use it for preserving the layout
    3. Follow the element hierarchy exactly as shown in the JSON
    4. Include all the text content from the "text" fields inside "content" field
    5. For images, use the file paths specified in the "media" fields. The file_path fields are given for you to use that path, do not try to add any random paths as it will not work. Use the file paths as they are given to you
        - For any element that includes a media file (such as an image or icon), the file path provided in "description.content.media.file_path" must be used exactly as it appears.
        - Do NOT generate or include any images, icons, logos, or visuals. Do not try to replicate visuals, illustrations, or inferred design elements. Your output must not contain any guessed or placeholder visual content.
        - Do not generate or guess new file paths. Use the given path directly in the HTML image `src` attribute.
    6. Ensure the layout does not differ from the original image.

    ## LAYOUT PRESERVATION STRATEGY
    All necessary layout and style information is provided in the JSON, and should be interpreted precisely without making assumptions beyond the data
    These are all the fields present in every element for you to consider so that you can generate a very accurate output :
        - Use the bounding-box and position data **only as a guide** for spacing, alignment, and hierarchy.
        - Don’t hard-lock the layout to the image’s aspect ratio—implement fluid, responsive layouts
        - Use the "description.styles.width" and "height" values in conjunction with the bounding boxes and Tailwind layout classes to ensure accurate scaling and spacing.
        - Take "%_position_parent" (the percentage position relative to its parent) and "%_position_body" (the percentage positon relative to the whole body) fields present in "description.layout" field of each element that contains "top", "right", "bottom", "left" values in percentage
        - Take "position_parent" and "position_body" fields present in "media.layout" field for media elements that contains "top", "right", "bottom", "left" values in pixels.
        - Ultimately take the "tailwind_classes" field present in "description.layout" field of each element to understand the positioning fixed/absolute/relative and other tailwind classes that are used to position the element

    All these above mentioned four fields are the REFERENCES for preserving the layout of the whole page. Once you understand these relationship blends and be able to convert this information to cater all the screen sizes you will be successfully able to preserve the layout for any screen size incorporating responsiveness, Our final layout must be adaptable to all the screen sizes.
    Understand the whole relationship structure using these the above mentioned fields and then take that information to preserve the layout in expansion or shrinking. Out final output must be responsive.

    Do NOT use absolute pixel values from the image dimensions directly in the final code. Use the coordinates and dimensions only to understand the proportional layout and spacing relationships between elements. The final implementation should be fully responsive and should not be fixed to the image's original width or height.

    - Carefully align each element based on its position and size from the JSON keeping in mind the responsiveness.
    - Double check each element’s placement and spacing by comparing it to the reference image — the final layout should have all the elements properly placed.
    - Do not shift or reflow elements unless specified by Tailwind’s responsive rules or required for mobile responsiveness.
    - Once you understand the layout, feel free to use flex and grids provided by tailwind classes to generate an output aligning to our needs of responsiveness and screenfullness.

    8. For color implementation, strictly follow the color palette provided in "description.styles.colorPalette" of each element. Colors are the most imprortant part of our implementation and the color choices must be very accurate from the given color palette.

    IMPORTANT INSTRUCTIONS FOR OUTPUT FORMAT:
    - Always wrap your HTML code in ```html code blocks.
    - Return only the complete HTML code with Tailwind classes, without any explanations outside the code blocks.
    - Return a complete, standalone HTML file that includes the Tailwind CSS CDN
    - The HTML should validate and be ready to render without any additional processing
    - Do not add any comments.
    - Include <!DOCTYPE html> and all required HTML tags
    - Include responsive viewport meta tag
    - Include appropriate font styling (use system fonts or Google Fonts if needed)

    IMPORTANT FOR ACCURACY:
    - Colors should exactly match those specified in the JSON color_palette field of each element.
    - All the layout information provided is with respect to the input image dimensions, we must adapt to all the screens accordingly, we should not be fixed to certain dimensions rigidly.
    - Text styling should strictly respect size, color, and weight as visible in the image.

    ## VALIDATION
    - Validate your generated code with the original image again to be sure of the color choices and design choices. Then provide the output once you are sure that you have generated the accurate depiction without any design flaws.
    - DO NOT TRY TO SHRINK THE OUTPUT LAYOUT TO MAKE IT LOOK IDENTICAL TO THE REFERENCE IMAGE. LET OUR LAYOUT BE FLUID AS THE SCREEN SIZE DEMANDS.

    ## JSON DESCRIPTION
    {{description}}

    Now, using the JSON description provided above and the Image that needs to be replicated, generate the complete HTML+Tailwind CSS code that perfectly replicates the interface.
    """
    
NON_HEURISTICS_GENERATE_CODE = f"""
    I'm providing you with both a UI image and its corresponding hierarchical structure in JSON format.
    
    Generate HTML and Tailwind CSS code for a UI based on the provided JSON structure and UI image.
    The JSON represents a hierarchy of UI elements along with their positioning and styles.
    Use the image as a reference for the layout and design.
    
    JSON Structure:
    {{description}}
    
    Create semantic HTML with appropriate Tailwind CSS classes that match the described styles.
    Pay attention to:
    1. Element nesting (parent-child relationships)
    2. Element types (div, header, button, etc.)
    3. CSS properties like dimensions, positioning, colors, etc.
    4. Use the provided image as a reference for the overall layout and design
    5. The JSON Schema is for your reference only, focus more on replicating the given UI image by using the JSON structure information.
    
    IMPORTANT INSTRUCTIONS FOR OUTPUT FORMAT:
    - Always wrap your HTML code in ```html code blocks.
    - Return only the complete HTML code with Tailwind classes, without any explanations outside the code blocks.
    - The HTML file should be a complete file with head and body tags including tailwind CDN.
    - MUST use the same colors, fonts, and layout as given in the JSON structure or as you depict from the given UI image for individual elements.
    - Use the paths given in the description for images, and do not attempt to replicate the actual content of images seen in the UI.
    - Also make sure that you use every image mentioned in the json at appropriate places in the HTML code.
    - STRICTLY Do not add any kind of comments in the generated code.
    
    IMPORTANT INSTRUCTIONS FOR IMAGE HANDLING:
    - For ALL images, use appropriate placeholder URLs or paths given in the JSON structure.
    - DO NOT attempt to replicate the actual content of images seen in the UI.
    - Maintain the relative dimensions and aspect ratios of image elements.
"""