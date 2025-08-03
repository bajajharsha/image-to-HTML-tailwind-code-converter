COMBINED_PROMPT = f"""
    I have {{len_html_files}} HTML code snippets from different portions of the same webpage.
    These snippets are in sequential order from top to bottom of the page.
    
    I need you to analyze all these snippets and combine them into a single, coherent HTML document.
    
    Guidelines:
    1. Identify the hierarchical structure of all snippets
    2. Determine the natural boundaries between each snippet
    3. Merge them intelligently to create a seamless, scrollable webpage
    4. Preserve all content, styles, and functionality
    5. Resolve any duplicate elements, overlapping structures, or conflicts
    6. Ensure the final HTML is valid and properly structured
    7. Don't use any kind of comments in the final HTML code.
    8. We are providing you html code snippets in chronological order, so you should strictly use the order to combine them.
    
    {{previous_code}}

    References:
    I am also providing you the original screenshots of the page sections for your reference to help you generate accurate final frontend.
    ```
    
    Please provide the combined HTML code that merges all these sections into one cohesive webpage.
    ONLY return the complete HTML code without any explanations.
    
    IMPORTANT INSTRUCTIONS FOR OUTPUT FORMAT: 
    - Always wrap your HTML code in ```html code blocks.
    - Return only the complete HTML code with Tailwind classes, without any explanations outside the code blocks.
"""