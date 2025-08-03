import React, { createContext, useState, useContext } from 'react';

const ConversionContext = createContext();

export const useConversion = () => useContext(ConversionContext);

export const ConversionProvider = ({ children }) => {
  const [generatedCode, setGeneratedCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [streamProgress, setStreamProgress] = useState([]);
  const [useHeuristic, setUseHeuristic] = useState(false); // Changed default to false (non-heuristic)

  // Helper function to add content to streaming state
  const appendToStreamingContent = (chunk) => {
    setStreamingContent(prev => {
      // Log for debugging
      console.log("Adding chunk to streaming content:", chunk);
      return prev + chunk;
    });
  };

  // Helper function to clear all states
  const clearStates = () => {
    setGeneratedCode('');
    setError(null);
    setStreamingContent('');
    setIsStreaming(false);
    setStreamProgress([]);
  };

  const value = {
    generatedCode,
    setGeneratedCode,
    isLoading,
    setIsLoading,
    error,
    setError,
    streamingContent,
    setStreamingContent,
    appendToStreamingContent,
    isStreaming,
    setIsStreaming,
    uploadedImage,
    setUploadedImage,
    streamProgress,
    setStreamProgress,
    useHeuristic,
    setUseHeuristic,
    clearStates,
  };

  return (
    <ConversionContext.Provider value={value}>
      {children}
    </ConversionContext.Provider>
  );
};