import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConversion } from '../../context/ConversionContext';
import Button from '../common/Button';

const Preview = () => {
  const { generatedCode } = useConversion();
  const [iframeKey, setIframeKey] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect if no code is available
    if (!generatedCode) {
      navigate('/');
    }
  }, [generatedCode, navigate]);

  const refreshPreview = () => {
    setIframeKey(prev => prev + 1);
  };

  if (!generatedCode) return null;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-500 dark:from-purple-400 dark:to-blue-400">
          Preview
        </h1>
        <div className="flex space-x-4">
          <Button
            onClick={refreshPreview}
            label="Refresh Preview"
            color="blue"
          />
          <Button
            onClick={() => navigate('/')}
            label="Back to Editor"
            color="gray"
          />
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 bg-opacity-90 dark:bg-opacity-80 backdrop-blur-sm rounded-xl shadow-lg p-4 h-[80vh] border border-gray-100 dark:border-gray-700 transition-all duration-300">
        <iframe
          key={iframeKey}
          srcDoc={generatedCode}
          title="Preview"
          className="w-full h-full border-none bg-white"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  );
};

export default Preview;