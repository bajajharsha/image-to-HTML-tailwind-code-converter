import React, { useState, useEffect } from 'react';

const ProgressIndicator = ({ progressMessages }) => {
  // Define the steps in our process with proper descriptions and relevant emojis
  const steps = [
    { id: 'analyzing', name: 'Analyzing Image', icon: '🔍', color: 'text-blue-500 dark:text-blue-400', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
    { id: 'processing', name: 'Processing Elements', icon: '⚙️', color: 'text-indigo-500 dark:text-indigo-400', bgColor: 'bg-indigo-100 dark:bg-indigo-900/30' },
    { id: 'generating', name: 'Generating Code', icon: '💻', color: 'text-purple-500 dark:text-purple-400', bgColor: 'bg-purple-100 dark:bg-purple-900/30' },
    { id: 'finalizing', name: 'Finalizing', icon: '✅', color: 'text-green-500 dark:text-green-400', bgColor: 'bg-green-100 dark:bg-green-900/30' }
  ];
  
  // Get message text safely from various message formats
  const getMessageText = (message) => {
    if (typeof message === 'string') {
      return message;
    }
    if (typeof message === 'object' && message !== null) {
      // Only return the message property, not the entire object
      return message.message || '';
    }
    return '';
  };
  
  // Check if a message contains specific text
  const messageContains = (message, searchText) => {
    const text = getMessageText(message);
    return typeof text === 'string' && text.includes(searchText);
  };
  
  // Filter out technical markers
  const shouldFilterMessage = (message) => {
    const text = getMessageText(message);
    return text.includes("[STARTING CODE GENERATION]") || 
           text.includes("[DONE]") ||
           text === '';
  };
  
  // Map messages to their corresponding step
  const getStepForMessage = (message) => {
    // If message is an object with phase property, use it
    if (typeof message === 'object' && message !== null && message.phase) {
      const phase = message.phase;
      if (phase === 'individual sections') return 'finalizing';
      return phase;
    }
    
    // Otherwise infer from message text
    const text = getMessageText(message);
    const cleanMessage = text.replace(/[\u{1F300}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '').trim();
    
    if (cleanMessage.includes('Analyzing')) return 'analyzing';
    if (cleanMessage.includes('Processing')) return 'processing';
    if (cleanMessage.includes('Generating') || cleanMessage.includes('Converting')) return 'generating';
    if (cleanMessage.includes('completed') || cleanMessage.includes('Complete') || cleanMessage.includes('Done') || cleanMessage.includes('Finalizing')) return 'finalizing';
    return 'processing'; // Default
  };
  
  // Get messages for a specific step
  const getMessagesForStep = (stepId) => {
    if (!progressMessages || !progressMessages.length) return [];
  
    // First filter to get relevant messages
    const filteredMessages = progressMessages
      .filter(message => {
        if (message === null || message === undefined) return false;
        if (shouldFilterMessage(message)) return false;
        
        // Special case for "individual sections" phase mapping to finalizing
        if (message.phase === 'individual sections' && stepId === 'finalizing') {
          return true;
        }
        
        return getStepForMessage(message) === stepId;
      });
  
    // Then map to get just the message text, cleaning as needed
    return filteredMessages.map(message => {
      // Extract just the message text from the object
      if (typeof message === 'object' && message !== null && message.message) {
        // If it's an object with a message property, use that
        return message.message;
      } else {
        // Otherwise use the whole message (for string messages)
        return message;
      }
    });
  };
  
  // Determine if a step is active
  const isStepActive = (stepId) => {
  if (!progressMessages || !progressMessages.length) return false;
  
  // Check if any message has this exact phase
  const hasExactPhaseActive = progressMessages.some(message => {
    if (message === null || message === undefined) return false;
    return getStepForMessage(message) === stepId;
  });
  
  // If we found a message for this exact phase, it's active
  if (hasExactPhaseActive) return true;
  
  // Special logic for phase transitions
  if (stepId === 'processing') {
    // If we have an analyzing message but no processing message,
    // and we also have a generating message, then processing must have happened
    const hasAnalyzingMessage = progressMessages.some(msg => 
      msg !== null && getStepForMessage(msg) === 'analyzing'
    );
    
    const hasGeneratingMessage = progressMessages.some(msg => 
      msg !== null && getStepForMessage(msg) === 'generating'
    );
    
    // If we have analysis and generation messages but no processing messages,
    // mark processing as active to show transition
    if (hasAnalyzingMessage && hasGeneratingMessage) return true;
  }
  
  return false;
};

// Determine if a step is completed
const isStepCompleted = (stepId) => {
  if (!progressMessages || !progressMessages.length) return false;

  // If a later phase is active, consider this phase completed
  const stepIndex = steps.findIndex(step => step.id === stepId);
  for (let i = stepIndex + 1; i < steps.length; i++) {
    if (isStepActive(steps[i].id)) {
      return true;
    }
  }

  // Otherwise look for completion messages for this phase
  return progressMessages.some(message => {
    if (message === null || message === undefined) return false;
    const phase = getStepForMessage(message);
    return phase === stepId && (
      messageContains(message, 'Done') || 
      messageContains(message, 'Complete') || 
      messageContains(message, 'completed')
    );
  });
  };
  
  // Determine the highest step we've reached
  const getHighestActiveStepIndex = () => {
    for (let i = steps.length - 1; i >= 0; i--) {
      if (isStepActive(steps[i].id)) {
        return i;
      }
    }
    return -1;
  };
  
  return (
    <div className="mb-6 bg-transparent p-6 transition-all duration-300">
      <h3 className="font-semibold text-gray-800 dark:text-gray-100 text-lg mb-5 flex items-center">
        <svg className="w-5 h-5 mr-2 text-purple-500 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Generation Progress
      </h3>
      
      <div className="space-y-4">
        {steps.map((step, index) => {
          const isActive = isStepActive(step.id);
          const isCompleted = isStepCompleted(step.id);
          const isReached = index <= getHighestActiveStepIndex();
          
          // Skip steps we haven't reached yet
          if (!isReached) return null;
          
          return (
            <div 
              key={step.id} 
              className={`p-3 rounded-lg border ${
                isCompleted 
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
                  : isActive 
                    ? `${step.bgColor} border-${step.color.split('-')[1]}-200 dark:border-${step.color.split('-')[1]}-800` 
                    : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
              } transition-all duration-300`}
            >
              <div className="flex items-center mb-2">
                <div className={`
                  flex items-center justify-center 
                  w-8 h-8 rounded-full mr-3
                  ${isCompleted 
                    ? 'bg-green-100 dark:bg-green-800 text-green-600 dark:text-green-300' 
                    : isActive 
                      ? `${step.bgColor} ${step.color}` 
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }
                  ${isActive && !isCompleted ? 'animate-pulse' : ''}
                `}>
                  <span>{step.icon}</span>
                </div>
                <span className={`font-medium 
                  ${isCompleted 
                    ? 'text-green-600 dark:text-green-400' 
                    : isActive 
                      ? 'text-gray-800 dark:text-gray-100' 
                      : 'text-gray-500 dark:text-gray-400'
                  }`}>
                  {step.name}
                </span>
                {isCompleted && (
                  <span className="ml-auto text-green-600 dark:text-green-400 flex items-center">
                    <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    Complete
                  </span>
                )}
                {isActive && !isCompleted && (
                  <span className="ml-auto">
                    <svg className="w-5 h-5 text-purple-500 dark:text-purple-400 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </span>
                )}
              </div>
              
              {/* Display messages for this step */}
              <div className="space-y-2 mt-3 ml-11 flex flex-col">
                {getMessagesForStep(step.id).map((message, msgIndex) => (
                  <div 
                    key={msgIndex}
                    className={`text-sm py-1.5 px-3 rounded-lg ${isCompleted 
                      ? 'bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-300' 
                      : `${step.bgColor} ${step.color}`
                    } mb-2`}
                  >
                    {message}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProgressIndicator;