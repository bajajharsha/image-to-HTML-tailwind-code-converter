import React, { useEffect, useRef, useState } from 'react';
import Button from '../../common/Button';

const PreviewRenderer = ({ htmlCode }) => {
  const [scale, setScale] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const iframeRef = useRef(null);
  const [viewportWidth, setViewportWidth] = useState('desktop');

  // Resize preview based on selected device type
  useEffect(() => {
    if (viewportWidth === 'mobile') {
      setScale(0.5);
    } else if (viewportWidth === 'tablet') {
      setScale(0.75);
    } else {
      setScale(1);
    }
  }, [viewportWidth]);

  // Handle iframe load event
  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  // Get appropriate width based on viewport selection
  const getIframeWidth = () => {
    switch(viewportWidth) {
      case 'mobile':
        return '375px';
      case 'tablet':
        return '768px';
      case 'desktop':
      default:
        return '100%';
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center mb-4 px-2">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setViewportWidth('mobile')}
            className={`p-2 rounded-md ${
              viewportWidth === 'mobile' 
                ? 'bg-purple-100 text-purple-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </button>
          <button
            onClick={() => setViewportWidth('tablet')}
            className={`p-2 rounded-md ${
              viewportWidth === 'tablet' 
                ? 'bg-purple-100 text-purple-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </button>
          <button
            onClick={() => setViewportWidth('desktop')}
            className={`p-2 rounded-md ${
              viewportWidth === 'desktop' 
                ? 'bg-purple-100 text-purple-700' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </button>
        </div>
        
        <Button
          onClick={() => {
            if (iframeRef.current) {
              iframeRef.current.src = 'about:blank';
              setTimeout(() => {
                iframeRef.current.srcdoc = htmlCode;
              }, 50);
            }
          }}
          label="Refresh Preview"
          color="blue"
          size="sm"
        />
      </div>
      
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75">
          <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-purple-700 border-opacity-50"></div>
        </div>
      )}
      
      <div 
        className="flex-grow flex items-center justify-center overflow-auto bg-gray-100 rounded-lg"
        style={{
          padding: viewportWidth !== 'desktop' ? '20px' : '0',
        }}
      >
        <div
          style={{
            transform: `scale(${scale})`,
            transformOrigin: 'top center',
            width: getIframeWidth(),
            height: viewportWidth !== 'desktop' ? '100%' : '100%',
            transition: 'all 0.3s ease',
          }}
          className="bg-white shadow-lg rounded-lg overflow-hidden"
        >
          <iframe
            ref={iframeRef}
            srcDoc={htmlCode}
            onLoad={handleIframeLoad}
            title="Generated webpage preview"
            className="w-full h-full border-none"
            sandbox="allow-scripts allow-same-origin"
          />
        </div>
      </div>
    </div>
  );
};

export default PreviewRenderer;