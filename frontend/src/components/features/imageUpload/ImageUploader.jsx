import React, { useRef, useState } from 'react';
import { useConversion } from '../../../context/ConversionContext';
import DragDropZone from './DragDropZone';
import Button from '../../common/Button';
import { convertImage, streamConvertImage } from '../../../services/api';

const ImageUploader = ({ conversionMode }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const {
    setGeneratedCode,
    setIsLoading,
    setError,
    setStreamingContent,
    setIsStreaming,
    uploadedImage,
    setUploadedImage,
    useHeuristic
  } = useConversion();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = (acceptedFiles) => {
    setIsDragging(false);
    if (acceptedFiles && acceptedFiles[0]) {
      processFile(acceptedFiles[0]);
    }
  };

  const processFile = (file) => {
    if (!file.type.match('image.*')) {
      setError('Please upload an image file');
      return;
    }
  
    // Create a FileReader to convert the file to a data URL
    const reader = new FileReader();
    reader.onload = (e) => {
      // e.target.result contains the data URL
      setUploadedImage(e.target.result);
      setError(null);
    };
    reader.onerror = () => {
      setError('Failed to read the image file');
    };
    reader.readAsDataURL(file);
  };

  const handleConversion = async () => {
    if (!uploadedImage) {
      setError('Please upload an image first');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      if (conversionMode === 'stream') {
        setIsStreaming(true);
        setStreamingContent('');
        
        const progressMessages = [];
        
        await streamConvertImage(
          dataURLtoFile(uploadedImage, 'upload.jpg'),
          useHeuristic,
          (chunk) => {
            // Update streaming content immediately for real-time display
            setStreamingContent(prev => prev + chunk);
          },
          (phase, message) => {
            if (message && !progressMessages.includes(message)) {
              progressMessages.push(message);
              console.log(`Progress update: ${message}`);
            }
          }
        );
        
        // The streamingContent is already updated in real-time
        
      } else {
        const result = await convertImage(dataURLtoFile(uploadedImage, 'upload.jpg'), useHeuristic);
        setGeneratedCode(result.code || '');
      }
    } catch (err) {
      setError(err.message || 'Failed to convert image');
    } finally {
      setIsLoading(false);
      // Keep isStreaming true if in streaming mode to continue showing the content
      if (conversionMode !== 'stream') {
        setIsStreaming(false);
      }
    }
  };

  // Helper function to convert data URL to File
  const dataURLtoFile = (dataUrl, filename) => {
    try {
      // Check if the dataUrl is in the expected format
      if (!dataUrl || typeof dataUrl !== 'string' || !dataUrl.startsWith('data:')) {
        throw new Error('Invalid data URL format');
      }
      
      const arr = dataUrl.split(',');
      if (arr.length < 2) {
        throw new Error('Invalid data URL format - missing comma separator');
      }
      
      const match = arr[0].match(/:(.*?);/);
      if (!match || match.length < 2) {
        throw new Error('Could not extract MIME type from data URL');
      }
      
      const mime = match[1];
      const bstr = atob(arr[1]);
      let n = bstr.length;
      const u8arr = new Uint8Array(n);
      while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
      }
      return new File([u8arr], filename, { type: mime });
    } catch (error) {
      console.error('Error converting data URL to file:', error);
      throw error;
    }
  };

  return (
    <div>
      <DragDropZone
        onDrop={handleDrop}
        isDragging={isDragging}
        setIsDragging={setIsDragging}
      >
        <div className="text-center p-6">
        {uploadedImage ? (
            <div className="mb-4">
              <img 
                src={uploadedImage} 
                alt="Preview" 
                className="max-h-60 mx-auto"
              />
            </div>
          ) : (
            <>
              <svg 
                className="mx-auto h-12 w-12 text-gray-400" 
                stroke="currentColor" 
                fill="none" 
                viewBox="0 0 48 48"
              >
                <path 
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4h-8m-12 0H8m36-12h-4m-8 0H8m36 0a4 4 0 00-4-4h-8m-12 0v20a4 4 0 004 4h20" 
                  strokeWidth="2" 
                  strokeLinecap="round"
                />
              </svg>
              <p className="mt-1 text-sm text-gray-600">
                Drag and drop your webpage image here, or click to select file
              </p>
            </>
          )}
          
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />
          
          <div className="mt-4 flex justify-center">
            {!uploadedImage ? (
              <Button
                onClick={() => fileInputRef.current.click()}
                label="Select File"
                color="blue"
              />
            ) : (
              <div className="flex space-x-4">
                <Button
                  onClick={() => fileInputRef.current.click()}
                  label="Change Image"
                  color="gray"
                />
                <Button
                  onClick={handleConversion}
                  label={conversionMode === 'stream' ? 'Stream Code Generation' : 'Generate Code'}
                  color="purple"
                />
              </div>
            )}
          </div>
        </div>
      </DragDropZone>
    </div>
  );
};

export default ImageUploader;