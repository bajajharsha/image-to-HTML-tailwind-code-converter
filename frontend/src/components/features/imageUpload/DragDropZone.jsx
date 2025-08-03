import React from 'react';

const DragDropZone = ({ children, onDrop, isDragging, setIsDragging }) => {
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    onDrop(files);
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg ${
        isDragging ? 'border-purple-500 bg-purple-50' : 'border-gray-300'
      } cursor-pointer transition-colors`}
    >
      {children}
    </div>
  );
};

export default DragDropZone;