import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/App.css';
import StartingPage from './components/StartingPage';
import ChatInterface from './components/ChatInterface';

function App() {
  const [hasEntered, setHasEntered] = useState(false);

  return (
    <div className="app-container">
      {!hasEntered ? (
        <StartingPage onEnter={() => setHasEntered(true)} />
      ) : (
        <ChatInterface />
      )}
    </div>
  );
}

export default App;