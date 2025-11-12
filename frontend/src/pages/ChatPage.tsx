import { useState, useRef, useEffect } from 'react';
import { Shield, Scroll, Sparkles } from 'lucide-react';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';
import { CybersichHeader } from '../components/CybersichHeader';
import * as chatApi from '../services/chat-api';
import type { Message } from '../types/chat';

// Background image - використовуємо як в .figma
const backgroundImage = '/2d76d3ed895b0324df0b5302921cd6c50e5b7a9e.png';

const initialMessages: Message[] = [
  {
    id: '1',
    content: 'Вітаю! Я — Cybersich AI, ваш помічник у цифровій Січі. Як я можу вам допомогти сьогодні?',
    role: 'assistant',
    timestamp: new Date(),
  },
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const session = await chatApi.createSession(
          'user_' + Date.now(),
          'Cybersich Chat'
        );
        setSessionId(session.session_id);
        console.log('✅ Session created:', session.session_id);
      } catch (err) {
        console.error('❌ Failed to create session:', err);
      }
    };
    initSession();
  }, []);

  const handleSendMessage = async (content: string) => {
    if (!sessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      // Send to backend (Писарь will record it)
      await chatApi.sendMessage(content, sessionId, 'user');

      // Simulate assistant response (Phase 1 - only Clerk)
      setTimeout(async () => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: getAIResponse(content),
          role: 'assistant',
          timestamp: new Date(),
        };

        // Record assistant message too
        await chatApi.sendMessage(aiMessage.content, sessionId, 'assistant');

        setMessages((prev) => [...prev, aiMessage]);
        setIsTyping(false);
      }, 1000 + Math.random() * 1500);
    } catch (err) {
      console.error('Failed to send message:', err);
      setIsTyping(false);
    }
  };

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
      <CybersichHeader 
        title="Cybersich" 
        subtitle="AI Помічник · Chat" 
      />
      
      <div className="max-w-7xl mx-auto h-[calc(100vh-80px)] flex flex-col pt-6">
        
        {/* Suggestion Cards */}
        {messages.length === 1 && (
          <div className="px-6 pb-6">
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
        <ChatInput onSend={handleSendMessage} disabled={!sessionId} />
      </div>
    </div>
  );
}

interface SuggestionCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}

function SuggestionCard({ 
  icon, 
  title, 
  description, 
  onClick 
}: SuggestionCardProps) {
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

function getAIResponse(_userMessage: string): string {
  const responses = [
    'Це чудове запитання! Дозвольте мені поділитися знаннями...',
    'За козацькими традиціями, мудрість передається з покоління в покоління...',
    'Наші предки навчали нас, що справжня сила — у єдності та честі...',
    'Історія показує, що відвага та рішучість завжди перемагають...',
    'Це нагадує мені одну давню козацьку притчу...',
  ];
  
  return responses[Math.floor(Math.random() * responses.length)];
}

