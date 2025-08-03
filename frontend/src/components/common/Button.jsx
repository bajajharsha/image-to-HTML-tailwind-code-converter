import React from 'react';
import { useTheme } from '../../context/ThemeContext';

const Button = ({ 
  label, 
  onClick, 
  color = 'blue', 
  size = 'md',
  disabled = false,
  type = 'button'
}) => {
  const { darkMode } = useTheme();
  
  const colorClasses = {
    blue: darkMode 
      ? 'bg-blue-600 hover:bg-blue-500 text-white'
      : 'bg-blue-500 hover:bg-blue-600 text-white',
    purple: darkMode
      ? 'bg-purple-500 hover:bg-purple-400 text-white'
      : 'bg-purple-600 hover:bg-purple-700 text-white',
    green: darkMode
      ? 'bg-green-600 hover:bg-green-500 text-white'
      : 'bg-green-500 hover:bg-green-600 text-white',
    gray: darkMode
      ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
      : 'bg-gray-200 hover:bg-gray-300 text-gray-800',
  };

  const sizeClasses = {
    sm: 'py-1 px-3 text-sm',
    md: 'py-2 px-4 text-base',
    lg: 'py-3 px-6 text-lg',
  };

  const focusRing = {
    blue: darkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-400',
    purple: darkMode ? 'focus:ring-purple-400' : 'focus:ring-purple-500',
    green: darkMode ? 'focus:ring-green-500' : 'focus:ring-green-400',
    gray: darkMode ? 'focus:ring-gray-600' : 'focus:ring-gray-400',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        ${colorClasses[color]} 
        ${sizeClasses[size]} 
        rounded-md font-medium transition-all duration-200
        focus:outline-none focus:ring-2 focus:ring-offset-2 ${focusRing[color]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        shadow-md hover:shadow-lg
      `}
    >
      {label}
    </button>
  );
};

export default Button;