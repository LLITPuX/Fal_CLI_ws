import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ChatHeader } from './ChatHeader';
import { Shield, Scroll, Sparkles } from 'lucide-react';
import type { Message, SuggestionCardProps } from '../types';

const initialMessages: Message[] = [
  {
    id: '1',
    content: 'Вітаю! Я — Cybersich AI, ваш помічник у цифровій Січі. Як я можу вам допомогти сьогодні?',
    role: 'assistant',
    timestamp: new Date(),
  },
];

export function ChatInterface(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async (content: string): Promise<void> => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: getAIResponse(content),
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1500);
  };

  return (
    <div className="max-w-5xl mx-auto h-screen flex flex-col">
      <ChatHeader />
      
      {/* Suggestion Cards */}
      {messages.length === 1 && (
        <div className="px-6 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
            <SuggestionCard
              icon={<Shield className="w-6 h-6" />}
              title="Історія Козацтва"
              description="Розкажи про славні традиції"
              onClick={() => handleSendMessage('Розкажи про історію козацтва')}
            />
            <SuggestionCard
              icon={<Scroll className="w-6 h-6" />}
              title="Мудрість Віків"
              description="Поради та знання предків"
              onClick={() => handleSendMessage('Поділись мудрістю предків')}
            />
            <SuggestionCard
              icon={<Sparkles className="w-6 h-6" />}
              title="Сучасність"
              description="Як це застосувати сьогодні"
              onClick={() => handleSendMessage('Як застосувати традиції сьогодні?')}
            />
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.slice(1).map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isTyping && (
            <div className="flex gap-3">
              <div 
                className="w-10 h-10 rounded-full flex items-center justify-center border-2"
                style={{ 
                  backgroundColor: '#FFD700',
                  borderColor: '#0057B7',
                }}
              >
                <Shield className="w-5 h-5" style={{ color: '#0057B7' }} />
              </div>
              <div 
                className="rounded-2xl rounded-tl-sm px-5 py-3"
                style={{ backgroundColor: '#2F2F27', color: '#F3EDDC' }}
              >
                <div className="flex gap-1">
                  <span className="animate-bounce" style={{ animationDelay: '0ms' }}>●</span>
                  <span className="animate-bounce" style={{ animationDelay: '150ms' }}>●</span>
                  <span className="animate-bounce" style={{ animationDelay: '300ms' }}>●</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <ChatInput onSend={handleSendMessage} />
    </div>
  );
}

function SuggestionCard({ 
  icon, 
  title, 
  description, 
  onClick 
}: SuggestionCardProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      className="p-5 rounded-lg border-2 hover:scale-105 transition-transform text-left"
      style={{
        borderColor: '#2F2F27',
        backgroundColor: '#F3EDDC',
      }}
    >
      <div 
        className="w-12 h-12 rounded-full flex items-center justify-center mb-3 border-2"
        style={{ 
          backgroundColor: '#FFD700',
          borderColor: '#0057B7',
        }}
      >
        <div style={{ color: '#0057B7' }}>{icon}</div>
      </div>
      <div style={{ color: '#2F2F27' }}>{title}</div>
      <div className="opacity-60 mt-1" style={{ color: '#2F2F27' }}>
        {description}
      </div>
    </button>
  );
}

function getAIResponse(userMessage: string): string {
  const responses = [
    'Це чудове запитання! Дозвольте мені поділитися знаннями...',
    'За козацькими традиціями, мудрість передається з покоління в покоління...',
    'Наші предки навчали нас, що справжня сила — у єдності та честі...',
    'Історія показує, що відвага та рішучість завжди перемагають...',
    'Це нагадує мені одну давню козацьку притчу...',
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
}