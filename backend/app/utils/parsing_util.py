import re


def extract_html(response_text: str) -> str:
    """
    Extracts HTML code from a string that contains a code block.
    
    :param response_text: The string containing the code block.
    
    :return: The extracted HTML code if found, otherwise the original string.
    """
    code_pattern = re.compile(r"```html\s*(.*?)\s*```", re.DOTALL)
    match = code_pattern.search(response_text)

    if match:
        return match.group(1)

    return response_text
