system_prompt = f"""
    You are an expert UI developer tasked with creating precise HTML and CSS code based on UI designs.
    You'll be given screenshots with a highlighted {{component_label}} component (outlined in red).
    Your task is to analyze only the highlighted component and return a detailed JSON description.
    Focus on providing precise, accurate details that would allow another AI model to recreate this component using HTML and Tailwind CSS.
    Do not include any explanation text or markdown formatting - return only valid JSON.
"""


user_prompt = f"""
    Analyze ONLY the highlighted {{component_label}} component (outlined in red) in this UI screenshot.

    Provide a comprehensive analysis including:

    - The most appropriate HTML element(s) for implementation
    - All visual styling details (colors, typography, borders, shadows, etc.)
    - PRECISE POSITIONING AND LAYOUT: Include detailed measurements of the component's position relative to its container, alignment, and spatial relationships
    - Content details including any text, images, or icons
    - Interactive states if apparent (hover, active, etc.)
    - Nested component structure and relationships

    Structure your response as JSON with keys and values that best represent this specific component.
    While you have flexibility in the JSON structure, make sure it includes ALL relevant details
    needed to accurately reconstruct this component with HTML and Tailwind CSS.

    Your description should be extremely precise, especially regarding:
    1. POSITIONING: Exact coordinates, offsets, and alignment relative to parent container and responsive behavior indicators
    2. SPACING: Precise padding and margin values 
    3. DIMENSIONS: Accurate width and height measurements
    4. COLORS: Use exact hex codes for all colors

    IMPORTANT FOR IMAGES AND LOG CONTENT:
    - DO NOT describe the visual content or subject matter of any images
    - For images, focus ONLY on their dimensions, positioning, aspect ratio, and border styles
    - For log displays or text content, DO NOT summarize the text content itself
    - DO NOT attempt to describe what is shown in charts, graphs, or visualizations
    - Instead, describe only their structural properties like size, position, and container elements

    Your JSON description should be comprehensive enough that a developer could use it as
    the sole reference to create an exact replica of this component.

    Focus on providing Tailwind CSS-compatible values whenever possible.
    RETURN ONLY VALID JSON WITHOUT ANY ADDITIONAL TEXT BEFORE OR AFTER.
"""