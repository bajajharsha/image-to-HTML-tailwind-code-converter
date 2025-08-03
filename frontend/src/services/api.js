const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const convertImage = async (imageFile, useHeuristic) => {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('use_heuristic', useHeuristic);  // Ensure boolean is properly passed as Form data

    console.log("Sending to convert endpoint with useHeuristic:", useHeuristic);

    const response = await fetch(`${API_BASE_URL}/convert`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to convert image');
    }

    const data = await response.json();
    console.log("API response:", data);
    return data;
  } catch (error) {
    console.error('Error converting image:', error);
    throw error;
  }
};

export const streamConvertImage = async (imageFile, useHeuristic, onChunkReceived, onProgressUpdate) => {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('use_heuristic', useHeuristic);  // Ensure boolean is properly passed as Form data

    console.log("Sending request to stream endpoint with useHeuristic:", useHeuristic);
    
    // Create a fetch request to the streaming endpoint
    const response = await fetch(`${API_BASE_URL}/convert/stream`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to stream conversion');
    }
    
    console.log("Response received, starting to process stream");
    
    // Get a reader from the response body stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let buffer = '';
    let done = false;
    let lastProcessTime = Date.now();
    const DELAY_BETWEEN_CHUNKS = 20; // reduced delay for smoother experience
    let completionSent = false;
    
    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      
      if (done) {
        console.log("Stream complete");
        
        // Check if there's any content in buffer that hasn't been processed
        if (buffer.trim()) {
          console.log("Processing final buffer content:", buffer);
          onChunkReceived && onChunkReceived(buffer + '\n');
        }
        
        // If we haven't seen a completion marker yet, add one
        if (!completionSent) {
          const completionMessage = '✅ Code Generation completed';
          console.log("Adding completion message");
          onChunkReceived && onChunkReceived('\n' + completionMessage + '\n');
          completionSent = true;
        }
        
        break;
      }
      
      // Decode the received chunk and add to buffer
      const text = decoder.decode(value, { stream: true });
      buffer += text;
      
      console.log("Received chunk:", text);
      
      // Process any complete messages in the buffer
      let processedBuffer = '';
      
      // Check for complete lines in the buffer
      const lines = buffer.split('\n');
      if (lines.length > 1) {
        // Process all but the last line (which might be incomplete)
        for (let i = 0; i < lines.length - 1; i++) {
          processLine(lines[i]);
        }
        // Keep the last line in the buffer
        buffer = lines[lines.length - 1];
      }
      
      // Process a single line of content
      function processLine(line) {
        if (!line.trim()) return;
        // Add artificial delay for visual effect
        const currentTime = Date.now();
        const timeElapsed = currentTime - lastProcessTime;
        if (timeElapsed < DELAY_BETWEEN_CHUNKS) {
          setTimeout(() => {
            processContent(line);
          }, DELAY_BETWEEN_CHUNKS - timeElapsed);
        } else {
          processContent(line);
        }
        lastProcessTime = Date.now();
      }
      
      // Process the actual content
      function processContent(content) {
        if (!content.trim()) return;
        // Check if it's an SSE message
        if (content.startsWith('data: ')) {
          content = content.slice(6);
        }
        // Try to parse as JSON if it looks like JSON
        if (content.trim().startsWith('{') && content.trim().endsWith('}')) {
          try {
            const jsonData = JSON.parse(content);
            console.log("Received JSON data:", jsonData);
            if (jsonData.error) {
              throw new Error(jsonData.error);
            } else if (jsonData.phase && jsonData.message) {
              // Send to update progress
              onProgressUpdate && onProgressUpdate(jsonData.phase, jsonData.message);
              // Send the JSON data to update content
              onChunkReceived && onChunkReceived(content + '\n');
              // Check for completion
              if (jsonData.message.includes('completed') || jsonData.message.includes('done')) {
                completionSent = true;
              }
            }
          } catch (e) {
            // Failed to parse as JSON - send raw
            console.log("Failed to parse as JSON:", e);
            onChunkReceived && onChunkReceived(content + '\n');
          }
        } else {
          // Not JSON formatted content
          if (
            content.startsWith('🔍') || 
            content.startsWith('💻') || 
            content.startsWith('⚙️') || 
            content.startsWith('✅') ||
            content.includes('Processing') ||
            content.includes('Analyzing') ||
            content.includes('Done') ||
            content.includes('Generating') ||
            content.includes('Converting') ||
            content.includes('Generation')
          ) {
            // This is a progress message
            console.log("Received progress message:", content);
            onProgressUpdate && onProgressUpdate(null, content);
          }
          // Always send the content
          onChunkReceived && onChunkReceived(content + '\n');
        }
      }
    }
  } catch (error) {
    console.error('Error streaming conversion:', error);
    throw error;
  }
};