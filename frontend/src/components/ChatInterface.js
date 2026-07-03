import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FaPlus, FaPaperPlane, FaTrash, FaTimes } from 'react-icons/fa';
import { Modal, Button } from 'react-bootstrap';
import { useDropzone } from 'react-dropzone';
import ChatMessage from './ChatMessage';
import SkeletonLoader from './SkeletonLoader';
import { uploadPDF, askQuestion, getDocuments, deleteDocument } from '../services/api';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
    // Add welcome message
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          text: '👋 Hello! Upload a PDF and ask me anything about its content.',
          sender: 'system',
          timestamp: new Date(),
        }
      ]);
    }
  }, []);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-resize textarea
  const handleInputChange = (e) => {
    setInputText(e.target.value);
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
  };

  // Load documents
  const loadDocuments = async () => {
    try {
      const result = await getDocuments();
      setDocuments(result.documents || []);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  // Handle file drop
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setUploadStatus(`Selected: ${acceptedFiles[0].name}`);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadStatus('Uploading...');

    try {
      const result = await uploadPDF(selectedFile);
      
      // Add success message
      setMessages(prev => [
        ...prev,
        {
          id: Date.now().toString(),
          text: `✅ Successfully uploaded and indexed "${selectedFile.name}" (${result.total_chunks} chunks)`,
          sender: 'system',
          timestamp: new Date(),
        }
      ]);

      setUploadStatus('Upload complete!');
      setSelectedFile(null);
      setShowUploadModal(false);
      
      // Refresh document list
      await loadDocuments();
      
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus(`❌ Upload failed: ${error.message || 'Unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  // Handle sending message
  const handleSendMessage = async () => {
    if (!inputText.trim() || loading) return;

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      text: inputText.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const response = await askQuestion(inputText.trim());

      // Add bot response
      const botMessage = {
        id: (Date.now() + 1).toString(),
        text: response.answer || 'No answer generated',
        sender: 'bot',
        timestamp: new Date(),
        sources: response.sources || [],
        chunksUsed: response.chunks_used || 0,
      };

      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      console.error('Question error:', error);
      
      // Add error message
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        text: `❌ Sorry, I couldn't process your question: ${error.message || 'Unknown error'}`,
        sender: 'system',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);

    } finally {
      setLoading(false);
    }
  };

  // Handle key press (Enter to send)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Delete document
  const handleDeleteDocument = async (docName) => {
    if (window.confirm(`Delete "${docName}"?`)) {
      try {
        await deleteDocument(docName);
        await loadDocuments();
        setMessages(prev => [
          ...prev,
          {
            id: Date.now().toString(),
            text: `🗑️ Deleted document: "${docName}"`,
            sender: 'system',
            timestamp: new Date(),
          }
        ]);
      } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete document');
      }
    }
  };

  return (
    <div className="chat-container">
      {/* Navbar */}
      <nav className="chat-navbar">
        <a className="navbar-brand" href="#">
          📚 PDF RAG Chatbot
        </a>
        <div className="d-flex align-items-center gap-3">
          <div className="navbar-docs">
            <span>📄 {documents.length} documents</span>
            {documents.length > 0 && (
              <div className="document-list">
                {documents.slice(0, 3).map((doc, idx) => (
                  <span key={idx} className="document-tag">
                    {doc.length > 20 ? doc.slice(0, 20) + '...' : doc}
                    <span 
                      className="remove-doc"
                      onClick={() => handleDeleteDocument(doc)}
                    >
                      <FaTimes size={10} />
                    </span>
                  </span>
                ))}
                {documents.length > 3 && (
                  <span className="document-tag">+{documents.length - 3} more</span>
                )}
              </div>
            )}
          </div>
          <button 
            className="btn btn-light btn-sm"
            onClick={() => setShowUploadModal(true)}
            style={{ 
              background: 'rgba(255,255,255,0.2)', 
              border: '1px solid rgba(255,255,255,0.3)',
              color: 'white',
              backdropFilter: 'blur(8px)'
            }}
          >
            <FaPlus /> Upload PDF
          </button>
        </div>
      </nav>

      {/* Messages */}
      <div className="messages-container">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        
        {/* Skeleton loader while loading */}
        {loading && <SkeletonLoader />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-container">
        <div className="input-wrapper">
          <button 
            className="upload-btn"
            onClick={() => setShowUploadModal(true)}
            title="Upload PDF"
          >
            <FaPlus />
          </button>
          
          <textarea
            ref={textareaRef}
            className="form-control"
            placeholder="Ask about your PDFs..."
            value={inputText}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            rows={1}
            disabled={loading}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'white',
              resize: 'none',
              padding: '0.5rem 0',
              minHeight: '44px',
            }}
          />
          
          <button
            className="send-btn"
            onClick={handleSendMessage}
            disabled={!inputText.trim() || loading}
          >
            <FaPaperPlane />
          </button>
        </div>
      </div>

      {/* Upload Modal */}
      <Modal
        show={showUploadModal}
        onHide={() => {
          setShowUploadModal(false);
          setSelectedFile(null);
          setUploadStatus('');
        }}
        centered
        className="file-upload-modal"
      >
        <Modal.Header closeButton style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <Modal.Title style={{ color: 'white' }}>
            <FaPlus /> Upload PDF
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            {selectedFile ? (
              <div>
                <div style={{ fontSize: '3rem' }}>📄</div>
                <div style={{ marginTop: '1rem', fontWeight: '500' }}>
                  {selectedFile.name}
                </div>
                <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '4rem' }}>📤</div>
                <div style={{ marginTop: '1rem', fontWeight: '500' }}>
                  Drag & drop a PDF here
                </div>
                <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>
                  or click to browse
                </div>
                <div style={{ fontSize: '0.75rem', opacity: 0.5, marginTop: '0.5rem' }}>
                  Max file size: 50MB
                </div>
              </div>
            )}
          </div>
          {uploadStatus && (
            <div style={{ 
              marginTop: '1rem', 
              padding: '0.75rem',
              background: 'rgba(255,255,255,0.1)',
              borderRadius: '8px',
              textAlign: 'center',
              color: 'white'
            }}>
              {uploadStatus}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <Button 
            variant="secondary" 
            onClick={() => {
              setShowUploadModal(false);
              setSelectedFile(null);
              setUploadStatus('');
            }}
            style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white' }}
          >
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            style={{ 
              background: 'rgba(135, 206, 235, 0.3)',
              border: '1px solid rgba(255,255,255,0.3)',
              color: 'white',
              backdropFilter: 'blur(8px)'
            }}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default ChatInterface;