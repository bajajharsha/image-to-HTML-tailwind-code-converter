BBOX_PROMPT = """
    You are a helpful assistant that detects UI elements in web screenshots.
    Detect all UI elements in this web screenshot that can help in generating a html skeleton. This would include elements like buttons, images, navbars, divs, input fields, headers, footers, sidebars, tables, forms, search bars and charts. But its not necessary to detect all of them but only the ones that canbe used to generate a html skeleton. And not a detailed one.
    Contain text into text_divs, as text is not a UI element and are generally written inside divs. If large amount of text is present that too close with each other, then create a single text_div for all of them instead of creating a text_div for each of them.
    Don't detect elements like link which are not significant.
    Label Icons as image.
    ALSO You have to Identify each and every div element with highest priority.
    Return ONLY a JSON list with format:
    [
      {{ "box_2d": [100, 200, 150, 300],"label": "button"}},
      {{ "box_2d": [400, 500, 450, 550],"label": "image"}}
    ]
    The box_2d should be [y_min, x_min, y_max, x_max] normalized to 0-1000, where [0,0] is the top-left corner.
"""

HEURISTIC_BBOX_PROMPT = """
    Analyze this screenshot of a news website and identify all visible UI elements with pixel-perfect bounding boxes.

    For each detected element, provide:
    1. A bounding box as [x_min, y_min, x_max, y_max] with **exact integer pixel values**.
    2. The element type (e.g., header, navbar, button, article, text block, etc.)
    3. A concise description of the element's content or purpose.

    Each detected element should have its own precise box, they must be precisely bound without any misalignments and with full accuracy.

    Critical requirements:
    - The bounding box coordinates must be **precise to the single pixel** — no rounding, guessing, or estimating.
    - Ensure: x_min < x_max and y_min < y_max for every bounding box.
    - Focus strictly on **visible** UI elements only.
    - Bounding boxes must **tightly fit** each element's visible area based on visual boundaries like edges, padding, background color shifts, borders, or margin spaces.
    - Parent elements must fully contain their child elements where appropriate (proper nesting).
    - **Pixel accuracy** is the top priority — double-check coordinate correctness before submitting.
    - Do not include extra commentary or non-visible elements (like hidden components).
    - Do not detect the text inside media elements such as logo/images/icons. The text inside such elements should not be included in the final output.

    Element types to detect:
    - header, logo, nav_link, icon, button
    - main_content_area, news_article, text_block, headline
    - image, video_player, sidebar
    - footer, link, search_box

    Format your response **only** as a JSON array, with each item containing:
    - `"bbox"`: list of 4 integers [y_min, x_min, y_max, x_max] normalized to 0-1000, where [0,0] is the top-left corner.
    - `"label"`: type of the UI element (string)
    - `"description"`: short text about its role or content (string)
    - `"text"`: text contained by that element. Condition: if the text extracted content belongs to the child then only assign that content to the child and do not add the same redundent content to its parent.
        For example, if there is a text block child then it should have the text content inside the text field of that particular text block, but the same text content should not be included in the text field of its own parent. Let the parent text content be an empty string if there is no independent text detected.
        

    Example format:
    [
      {"bbox": [219, 284, 261, 714], "label":"header", "description": "Top navigation bar","text":"Example extracted text"}
      {"bbox": [27, 438, 81, 564], "label":"logo", "description": "ABC News logo", "text":""}
    ]

    **Only output the JSON array. Do not include any explanation, introduction, or extra text.**
"""