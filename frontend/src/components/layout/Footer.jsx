import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-gradient-to-r from-white to-blue-50 dark:from-gray-900 dark:to-blue-950 border-t border-gray-200 dark:border-gray-800 py-6 transition-colors duration-300">
      <div className="container mx-auto px-4">
        <div className="text-center text-gray-500 dark:text-gray-400 text-sm">
          <p>© {new Date().getFullYear()} Image to Code Converter. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;