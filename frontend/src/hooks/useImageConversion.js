import { useState } from 'react';
import { convertImage, streamConvertImage } from '../services/api';

export const useImageConversion = () => {
  const [generatedCode, setGeneratedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const clearState = () => {
    setGeneratedCode('');
    setStreamingContent('');
    setError(null);
  };

  const handleImageConversion = async (imageFile, useStreaming = false) => {
    if (!imageFile) {
      setError('No image file provided');
      return;
    }

    clearState();
    setIsLoading(true);

    try {
      if (useStreaming) {
        setIsStreaming(true);
        await streamConvertImage(imageFile, chunk => {
          setStreamingContent(prev => prev + chunk);
        });
      } else {
        const result = await convertImage(imageFile);
        setGeneratedCode(result.code || '');
      }
    } catch (err) {
      setError(err.message || 'Failed to convert image');
    } finally {
      setIsLoading(false);
      if (useStreaming) {
        setIsStreaming(false);
      }
    }
  };

  return {
    generatedCode,
    isLoading,
    error,
    streamingContent,
    isStreaming,
    handleImageConversion,
    clearState,
  };
};