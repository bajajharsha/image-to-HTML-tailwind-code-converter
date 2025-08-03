/**
 * Utility functions for formatting and handling code
 */

/**
 * Extracts HTML code from a mixed text response
 * @param {string} text - The text to extract HTML from
 * @returns {string} - The extracted HTML code
 */
export const extractHtmlCode = (text) => {
    // Try to extract code between HTML tags
    if (text.includes('<html') && text.includes('</html>')) {
      const startIndex = text.indexOf('<html');
      const endIndex = text.indexOf('</html>') + 7;
      return text.substring(startIndex, endIndex);
    }
    
    // Try to extract code between markdown code blocks
    if (text.includes('```html') && text.includes('```')) {
      const startIndex = text.indexOf('```html') + 7;
      const endIndex = text.lastIndexOf('```');
      if (startIndex > 7 && endIndex > startIndex) {
        return text.substring(startIndex, endIndex).trim();
      }
    }
    
    // If no HTML structure is found but there are HTML tags, try to clean up
    if (text.includes('<') && text.includes('>')) {
      // Remove any non-HTML content at the beginning
      let cleanText = text;
      if (!text.trim().startsWith('<')) {
        const firstTagIndex = text.indexOf('<');
        cleanText = text.substring(firstTagIndex);
      }
      
      // Remove any non-HTML content at the end
      if (!cleanText.trim().endsWith('>')) {
        const lastTagIndex = cleanText.lastIndexOf('>');
        cleanText = cleanText.substring(0, lastTagIndex + 1);
      }
      
      return cleanText;
    }
    
    // If we can't determine HTML structure, return the original text
    return text;
  };
  
  /**
   * Formats HTML code with proper indentation
   * @param {string} html - The HTML to format
   * @returns {string} - The formatted HTML
   */
  export const formatHtml = (html) => {
    let formatted = '';
    let indent = 0;
    
    // Simple HTML formatting logic
    html = html.replace(/>\s*</g, '>\n<'); // Add new line between tags
    
    html.split('\n').forEach(line => {
      line = line.trim();
      if (!line) return;
      
      // Decrease indent for closing tags
      if (line.match(/^<\/\w/)) {
        indent -= 2;
        indent = Math.max(0, indent); // Prevent negative indent
      }
      
      // Add the line with proper indentation
      formatted += ' '.repeat(indent) + line + '\n';
      
      // Increase indent for opening tags, unless they're self-closing or special tags
      if (line.match(/^<\w/) && 
          !line.match(/\/>$/) && 
          !line.match(/^<(img|br|hr|input|link|meta)/)) {
        indent += 2;
      }
    });
    
    return formatted;
  };
  
  /**
   * Adds missing elements to ensure HTML is valid
   * @param {string} html - The HTML to validate
   * @returns {string} - Valid HTML with required elements
   */
  export const validateHtml = (html) => {
    let validHtml = html.trim();
    
    // Add HTML tag if missing
    if (!validHtml.includes('<html')) {
      if (!validHtml.includes('<head')) {
        validHtml = `<html>\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Generated Webpage</title>\n</head>\n${validHtml}</html>`;
      } else {
        validHtml = `<html>\n${validHtml}</html>`;
      }
    }
    
    // Add body tag if missing
    if (!validHtml.includes('<body')) {
      // Find where to insert body tag
      const headEndIndex = validHtml.indexOf('</head>');
      if (headEndIndex !== -1) {
        const beforeBody = validHtml.substring(0, headEndIndex + 7);
        const afterHead = validHtml.substring(headEndIndex + 7);
        validHtml = `${beforeBody}\n<body>\n${afterHead}\n</body>`;
      } else {
        // No head tag, insert after html tag
        const htmlTagIndex = validHtml.indexOf('>');
        if (htmlTagIndex !== -1) {
          const beforeBody = validHtml.substring(0, htmlTagIndex + 1);
          const afterHtml = validHtml.substring(htmlTagIndex + 1);
          validHtml = `${beforeBody}\n<body>\n${afterHtml}\n</body>`;
        }
      }
    }
    
    return validHtml;
  };