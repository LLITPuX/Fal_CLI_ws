import { useState } from 'react';
import { ChatInterface } from './components/ChatInterface';
import backgroundImage from 'figma:asset/2d76d3ed895b0324df0b5302921cd6c50e5b7a9e.png';

export default function App() {
  return (
    <div 
      className="min-h-screen relative"
      style={{
        backgroundImage: `linear-gradient(rgba(243, 237, 220, 0.75), rgba(243, 237, 220, 0.75)), url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <ChatInterface />
    </div>
  );
}
