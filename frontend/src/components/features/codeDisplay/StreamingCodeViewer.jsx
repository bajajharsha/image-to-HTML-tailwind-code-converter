import React, { useEffect, useRef, useState } from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import html from 'react-syntax-highlighter/dist/esm/languages/hljs/xml';
import { a11yDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import Button from '../../common/Button';
import { useConversion } from '../../../context/ConversionContext';
import { useTheme } from '../../../context/ThemeContext';
import ProgressIndicator from './ProgressIndicator.jsx';

SyntaxHighlighter.registerLanguage('html', html);

const TypewriterCursor = ({ isTypingComplete }) => {
  const [visible, setVisible] = useState(true);
  
  useEffect(() => {
    // Only blink if typing is not complete
    if (isTypingComplete) return;
    
    const interval = setInterval(() => {
      setVisible(prev => !prev);
    }, 500);
    
    return () => clearInterval(interval);
  }, [isTypingComplete]);
  
  // Don't show cursor at all if typing is complete
  if (isTypingComplete) return null;
  
  return <span className={`text-white ${visible ? 'opacity-100' : 'opacity-0'}`}>|</span>;
};

const StreamingCodeViewer = ({ content }) => {
  const containerRef = useRef(null);
  const [processedContent, setProcessedContent] = useState('');
  const [progressMessages, setProgressMessages] = useState([]);
  const [isTypingComplete, setIsTypingComplete] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const { setGeneratedCode } = useConversion();
  const { darkMode } = useTheme();
  
  // Auto-scroll to bottom when content updates
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [processedContent]);
  
  // Process the incoming content
  useEffect(() => {
    if (!content) return;
    
    const lines = content.split('\n');
    const newProgressMessages = [];
    let codeContent = '';
    
    // Process each line
    const parseSingleQuotedJson = (text) => {
      try {
        // First replace single quotes with double quotes, but handle escape sequences properly
        // This regex handles most cases of single-quoted JSON-like strings
        const doubleQuoted = text
          .replace(/'/g, '"')
          .replace(/\\"/g, "\\'"); // Fix any escaped quotes
        
        return JSON.parse(doubleQuoted);
      } catch (e) {
        console.log("Failed to parse JSON-like string", e);
        return null;
      }
    };
    
    // Process each line
    lines.forEach(line => {
      try {
        if (line.trim().startsWith('{') && line.trim().endsWith('}')) {
          let jsonData;
          try {
            // Try standard JSON parsing first
            jsonData = JSON.parse(line);
          } catch (e) {
            // If that fails, try our custom parser for single-quoted JSON
            jsonData = parseSingleQuotedJson(line);
            if (!jsonData) throw new Error("Invalid JSON format");
          }
          
          if (jsonData.phase && jsonData.message) {
            // It's a structured progress message
            let messageText = jsonData.message;
            
            // Check if the message itself is a JSON string (nested JSON)
            if (typeof messageText === 'string' && 
                (messageText.includes("'phase':") || messageText.includes('"phase":'))) {
              
              // Try to extract just the inner message from the nested JSON-like string
              const innerData = parseSingleQuotedJson(messageText);
              if (innerData && innerData.message) {
                messageText = innerData.message;
              }
            }
            
            newProgressMessages.push({
              phase: jsonData.phase,
              message: messageText,
              sequence: jsonData.sequence || 0
            });
            
            // Check if code generation is complete
            if (jsonData.phase === 'finalizing' || 
              (jsonData.phase === 'individual sections' && messageText.includes('completed'))) {
              setIsTypingComplete(true);
              setGeneratedCode(codeContent);
            }
          }
        } else {
          throw new Error("Not valid JSON");
        }
      } catch (e) {
        if (
          line.startsWith('🔍') || 
          line.startsWith('💻') || 
          line.startsWith('⚙️') || 
          line.startsWith('✅') ||
          line.includes('Processing') ||
          line.includes('Analyzing') ||
          line.includes('Done') ||
          line.includes('Generating') ||
          line.includes('Converting') ||
          line.includes('Generation')
        ) {
          if (
            !line.includes("[STARTING CODE GENERATION]") && 
            !line.includes("[DONE]") &&
            line.trim() !== ''
          ) {
            // It's a progress message - add with an inferred phase
            const phase = inferPhaseFromMessage(line);
            newProgressMessages.push({
              phase,
              message: line,
              sequence: newProgressMessages.length // use array length as sequence for backward compatibility
            });
          }
          
          // Check if code generation is complete
          if (line.includes('✅ Code Generation completed')) {
            setIsTypingComplete(true);
            // Set the generated code in context for preview
            setGeneratedCode(codeContent);
          }
        } else if (line.trim() !== '') {
          // It's code content
          if (!line.includes("[STARTING CODE GENERATION]") && !line.includes("[DONE]")) {
            codeContent += line + '\n';
          }
        }
      }
    });

    // Sort progress messages by sequence
    newProgressMessages.sort((a, b) => a.sequence - b.sequence);
    
    setProgressMessages(newProgressMessages);
    setProcessedContent(codeContent);
  }, [content, setGeneratedCode]);

  const inferPhaseFromMessage = (message) => {
    const cleanMessage = message.toLowerCase();
    if (cleanMessage.includes('analyzing')) return 'analyzing';
    if (cleanMessage.includes('processing')) return 'processing';
    if (cleanMessage.includes('generating') || cleanMessage.includes('converting')) return 'generating';
    if (cleanMessage.includes('completed') || cleanMessage.includes('done') || cleanMessage.includes('finalizing')) return 'finalizing';
    return 'processing'; // Default
  };
  
  const handleCopy = () => {
    navigator.clipboard.writeText(processedContent);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };
  
  return (
    <div className="space-y-4">
      {/* Progress Messages */}
      {progressMessages.length > 0 && (
        <ProgressIndicator progressMessages={progressMessages} />
      )}
      
      {/* Copy Code Button - Always show it, but only enabled when there's content */}
      <div className="flex justify-end mb-2">
        <Button
          onClick={handleCopy}
          label={isCopied ? 'Copied!' : 'Copy Code'}
          color={isCopied ? 'green' : 'blue'}
          size="sm"
          disabled={!processedContent}
        />
      </div>
      
      {/* Code Display with Typewriter Effect */}
      <div 
        ref={containerRef}
        className="overflow-auto max-h-[500px] rounded-lg relative shadow-inner"
      >
        <div className="absolute right-2 top-2 z-10 bg-gray-800 dark:bg-gray-900 text-xs px-2 py-1 rounded text-gray-300 dark:text-gray-200">
          {isTypingComplete ? 'Generation Complete' : 'Real-time Generation'}
        </div>
        
        <div className="relative">
          <SyntaxHighlighter
            language="html"
            style={a11yDark}
            customStyle={{
              borderRadius: '0.5rem',
              padding: '1rem',
              fontSize: '0.9rem',
              whiteSpace: 'pre',
              overflowX: 'auto',
              backgroundColor: darkMode ? '#1e293b' : '#1a1a1a',
            }}
            wrapLines={true}
            showLineNumbers={false}
          >
            {processedContent}
          </SyntaxHighlighter>
          
          {/* Add the blinking cursor at the end of the code only if typing isn't complete */}
          {!isTypingComplete && processedContent && (
            <div className="absolute bottom-4 left-[calc(1rem)]">
              <TypewriterCursor isTypingComplete={isTypingComplete} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StreamingCodeViewer;