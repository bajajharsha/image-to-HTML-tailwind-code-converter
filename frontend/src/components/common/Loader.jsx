import React from 'react';

const Loader = () => {
  return (
    <div className="flex justify-center items-center py-12">
      <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-purple-600 dark:border-purple-400 border-opacity-80"></div>
    </div>
  );
};

export default Loader;