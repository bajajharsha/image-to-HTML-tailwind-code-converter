import React, { useState, useEffect } from 'react';
import { useConversion } from '../../context/ConversionContext';
import ImageUploader from '../features/imageUpload/ImageUploader';
import CodeViewer from '../features/codeDisplay/CodeViewer';
import StreamingCodeViewer from '../features/codeDisplay/StreamingCodeViewer';
import Button from '../common/Button';
import Loader from '../common/Loader';
import ErrorMessage from '../common/ErrorMessage';

const Toggle = ({ isEnabled, onToggle, labelLeft, labelRight }) => {
  return (
    <div className="flex items-center space-x-3">
      <span className={`text-sm ${!isEnabled 
        ? 'font-medium text-gray-800 dark:text-gray-100' 
        : 'text-gray-600 dark:text-gray-400'}`}
      >
        {labelLeft}
      </span>
      
      <button 
        onClick={onToggle}
        className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors duration-300 focus:outline-none ${
          isEnabled 
            ? 'bg-purple-600 dark:bg-purple-500' 
            : 'bg-gray-300 dark:bg-gray-600'
        }`}
        aria-checked={isEnabled}
        role="switch"
      >
        <span 
          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition-transform duration-300 ease-in-out ${
            isEnabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
      
      <span className={`text-sm ${isEnabled 
        ? 'font-medium text-gray-800 dark:text-gray-100' 
        : 'text-gray-600 dark:text-gray-400'}`}
      >
        {labelRight}
      </span>
    </div>
  );
};

const Home = () => {
  const {
    generatedCode,
    isLoading,
    error,
    isStreaming,
    streamingContent,
    clearStates,
    useHeuristic,
    setUseHeuristic
  } = useConversion();
  // Changed the initial default to 'stream' instead of 'standard'
  const [conversionMode, setConversionMode] = useState('stream'); 
  const [activeInfo, setActiveInfo] = useState(null); // Which info to show: 'mode' or 'method'

  // Reset states when switching conversion modes
  useEffect(() => {
    clearStates();
  }, [conversionMode]);

  // Logic is reversed - now isEnabled is true when 'standard', not 'stream'
  const handleToggleMode = () => {
    setConversionMode(prevMode => prevMode === 'stream' ? 'standard' : 'stream');
  };
  
  const handleToggleHeuristic = () => {
    setUseHeuristic(prev => !prev);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8 text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-500 dark:from-purple-400 dark:to-blue-400">
          Image to Code Converter
        </h1>
        
        <div className="bg-white dark:bg-gray-800 bg-opacity-90 dark:bg-opacity-80 backdrop-blur-sm rounded-xl shadow-lg p-6 mb-8 border border-gray-100 dark:border-gray-700 transition-all duration-300">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-5">
            <h2 className="text-xl font-semibold mb-3 md:mb-0 text-gray-800 dark:text-gray-200">Upload Your Webpage Image</h2>
          </div>
          
          {/* Simplified Settings Panel */}
          <div className="mb-6">
            <div className="rounded-lg border border-gray-200 dark:border-gray-600 mb-4 overflow-hidden">
              {/* Settings Header */}
              <div className="bg-gray-50 dark:bg-gray-700 p-3 border-b border-gray-200 dark:border-gray-600">
                <h3 className="font-medium text-gray-800 dark:text-gray-100 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-purple-600 dark:text-purple-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                  </svg>
                  Conversion Settings
                </h3>
              </div>
              
              {/* Settings Controls */}
              <div className="p-4">
                <div className="flex flex-col space-y-4 sm:flex-row sm:space-y-0 sm:space-x-6 sm:justify-center">
                  {/* Conversion Mode Toggle - Swapped labels */}
                  <div 
                    className="flex flex-col items-center bg-white dark:bg-gray-700 p-3 rounded-lg shadow-sm border border-gray-100 dark:border-gray-600"
                    onMouseEnter={() => setActiveInfo('mode')}
                    onClick={() => setActiveInfo('mode')}
                  >
                    <div className="text-2xl mb-2"></div>
                    <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Conversion Mode</h4>
                    <Toggle 
                      isEnabled={conversionMode === 'standard'} // Reversed logic here
                      onToggle={handleToggleMode}
                      labelLeft="Stream" // Swapped positions
                      labelRight="Standard" // Swapped positions
                    />
                  </div>
                  
                  {/* Generation Method Toggle */}
                  <div 
                    className="flex flex-col items-center bg-white dark:bg-gray-700 p-3 rounded-lg shadow-sm border border-gray-100 dark:border-gray-600"
                    onMouseEnter={() => setActiveInfo('method')}
                    onClick={() => setActiveInfo('method')}
                  >
                    <div className="text-2xl mb-2"></div>
                    <h4 className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">Generation Method</h4>
                    <Toggle 
                      isEnabled={useHeuristic}
                      onToggle={handleToggleHeuristic}
                      labelLeft="Non-heuristic"
                      labelRight="Heuristic"
                    />
                  </div>
                </div>
                
                {/* Settings Info Panel - Separate Container */}
                {(activeInfo === 'mode' || activeInfo === 'method') && (
                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 transition-all duration-300">
                    {activeInfo === 'mode' && (
                      <div className="text-sm text-gray-700 dark:text-gray-300">
                        <div className="font-medium mb-1">
                          {conversionMode === 'standard' ? 'Standard Mode' : 'Stream Mode'}
                        </div>
                        <p>
                          {conversionMode === 'standard' 
                            ? "Shows the complete code only after generation is finished." 
                            : "Displays the code generation process in real-time with live updates."}
                        </p>
                      </div>
                    )}
                    
                    {activeInfo === 'method' && (
                      <div className="text-sm text-gray-700 dark:text-gray-300">
                        <div className="font-medium mb-1">
                          {useHeuristic ? 'Heuristic Method' : 'Non-heuristic Method'}
                        </div>
                        <p>
                          {useHeuristic 
                            ? "Uses faster rule-based generation with better performance." 
                            : "Uses AI-powered generation with greater accuracy and detail."}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <ImageUploader conversionMode={conversionMode} />
        </div>
        
        {error && <ErrorMessage message={error} />}
        
        {isLoading && !isStreaming && <Loader />}
        
        {isStreaming && (
          <div className="bg-white dark:bg-gray-800 bg-opacity-90 dark:bg-opacity-80 backdrop-blur-sm rounded-xl shadow-lg p-6 mb-8 border border-gray-100 dark:border-gray-700 transition-all duration-300">
            <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-200 flex items-center">
              <span className="mr-2">💻</span>
              Streaming Code Generation
              {isLoading && <span className="ml-2 inline-block animate-pulse">⚡</span>}
            </h2>
            <StreamingCodeViewer content={streamingContent} />
          </div>
        )}

        {!isLoading && !isStreaming && generatedCode && (
          <div className="bg-white dark:bg-gray-800 bg-opacity-90 dark:bg-opacity-80 backdrop-blur-sm rounded-xl shadow-lg p-6 mb-8 border border-gray-100 dark:border-gray-700 transition-all duration-300">
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 flex items-center">
                <span className="mr-2">📝</span>
                Generated Code
              </h2>
            </div>
            <CodeViewer code={generatedCode} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;