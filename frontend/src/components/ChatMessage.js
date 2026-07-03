import React, { useState } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import { FaCopy, FaCheck } from 'react-icons/fa';

const ChatMessage = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender === 'user';
  const isSystem = message.sender === 'system';

  const handleCopy = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isSystem) {
    return (
      <div className="message-wrapper system">
        <div className="message-bubble system">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'bot'}`}>
      <div className={`message-bubble ${isUser ? 'user' : 'bot'}`}>
        <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {message.text}
        </div>

        {/* Sources for bot messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="sources-container">
            <div className="sources-title">📚 Sources</div>
            {message.sources.map((source, index) => (
              <div key={index} className="source-item">
                <span className="source-icon">•</span>
                <span>{source.document}</span>
                {source.relevance_score && (
                  <span style={{ opacity: 0.5 }}>
                    ({Math.round(source.relevance_score * 100)}% confidence)
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {!isUser && message.chunksUsed > 0 && (
          <div style={{ 
            fontSize: '0.7rem', 
            opacity: 0.4, 
            marginTop: '0.5rem' 
          }}>
            Used {message.chunksUsed} chunks to answer
          </div>
        )}

        {/* Action buttons */}
        <div className="message-actions">
          <CopyToClipboard text={message.text} onCopy={handleCopy}>
            <button title="Copy">
              {copied ? <FaCheck size={12} /> : <FaCopy size={12} />}
            </button>
          </CopyToClipboard>
        </div>
      </div>
      
      <div className="message-timestamp">
        {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : ''}
      </div>
    </div>
  );
};

export default ChatMessage;