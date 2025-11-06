import React from 'react';
import { Shield, User } from 'lucide-react';
import type { ChatMessageProps } from '../types';

export function ChatMessage({ message }: ChatMessageProps): JSX.Element {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={`flex gap-3 ${!isAssistant ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div 
        className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border-2"
        style={{ 
          backgroundColor: '#FFD700',
          borderColor: '#0057B7',
        }}
      >
        {isAssistant ? (
          <Shield className="w-5 h-5" style={{ color: '#0057B7' }} />
        ) : (
          <User className="w-5 h-5" style={{ color: '#0057B7' }} />
        )}
      </div>

      {/* Message Bubble */}
      <div 
        className={`rounded-2xl px-5 py-3 max-w-2xl ${
          isAssistant ? 'rounded-tl-sm' : 'rounded-tr-sm'
        }`}
        style={{
          backgroundColor: isAssistant ? '#2F2F27' : '#0057B7',
          color: isAssistant ? '#F3EDDC' : '#FFFFFF',
        }}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>
        <div 
          className="mt-2 opacity-50"
        >
          {message.timestamp.toLocaleTimeString('uk-UA', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
}