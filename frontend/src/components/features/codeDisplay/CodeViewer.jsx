import React, { useState } from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import html from 'react-syntax-highlighter/dist/esm/languages/hljs/xml';
import { a11yDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import Button from '../../common/Button';
import { useTheme } from '../../../context/ThemeContext';

SyntaxHighlighter.registerLanguage('html', html);

const CodeViewer = ({ code }) => {
  const [isCopied, setIsCopied] = useState(false);
  const { darkMode } = useTheme();

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <div className="relative">
      <div className="absolute right-2 top-2 z-10">
        <Button
          onClick={handleCopy}
          label={isCopied ? 'Copied!' : 'Copy Code'}
          color={isCopied ? 'green' : 'blue'}
          size="sm"
        />
      </div>
      <div className="overflow-auto max-h-[500px] rounded-lg shadow-inner">
        <SyntaxHighlighter
          language="html"
          style={a11yDark}
          customStyle={{
            borderRadius: '0.5rem',
            padding: '1rem',
            fontSize: '0.9rem',
            backgroundColor: darkMode ? '#1e293b' : '#1a1a1a',
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export default CodeViewer;