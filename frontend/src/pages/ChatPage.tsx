import { useState, useRef, useEffect } from 'react';
import { Shield, Sparkles, Scroll } from 'lucide-react';
import * as chatApi from '../services/chat-api';
import { ChatHeader } from '../components/chat/ChatHeader';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [error, setError] = useState<string>('');
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
        console.log('Session created:', session.session_id);
      } catch (err) {
        console.error('Failed to create session:', err);
        setError('Не вдалося ініціалізувати сесію чату');
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

      // Simulate assistant response for now (Phase 1 - only Clerk)
      setTimeout(async () => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: 'Дякую за ваше повідомлення! Писарь успішно записав його в граф знань. ' +
                   'В Phase 2 (Підсвідомість) та Phase 3 (Оркестратор) я зможу відповідати на основі контексту всієї історії.',
          role: 'assistant',
          timestamp: new Date(),
        };

        // Record assistant message too
        await chatApi.sendMessage(aiMessage.content, sessionId, 'assistant');

        setMessages((prev) => [...prev, aiMessage]);
        setIsTyping(false);
      }, 1500);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Не вдалося відправити повідомлення');
      setIsTyping(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  return (
    <div 
      className="min-h-screen relative"
      style={{
        backgroundImage: `linear-gradient(rgba(243, 237, 220, 0.75), rgba(243, 237, 220, 0.75)), url(/chat-background.png)`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundColor: '#F3EDDC',
        margin: 0,
        padding: 0,
      }}
    >
      <div className="h-screen flex flex-col" style={{ maxWidth: 'none', margin: 0 }}>
        <ChatHeader />

        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-100 border-2 border-red-500 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Suggestion Cards - показуємо коли немає повідомлень */}
        {messages.length === 0 && !isTyping && (
          <div className="px-6 py-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
              <SuggestionCard
                icon={<Shield className="w-6 h-6" />}
                title="Історія Козацтва"
                description="Розкажи про славні традиції"
                onClick={() => handleSuggestionClick('Розкажи про історію козацтва')}
              />
              <SuggestionCard
                icon={<Scroll className="w-6 h-6" />}
                title="Мудрість Віків"
                description="Поради та знання предків"
                onClick={() => handleSuggestionClick('Поділись мудрістю предків')}
              />
              <SuggestionCard
                icon={<Sparkles className="w-6 h-6" />}
                title="Сучасність"
                description="Як це застосувати сьогодні"
                onClick={() => handleSuggestionClick('Як застосувати традиції сьогодні?')}
              />
            </div>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((message) => (
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

function SuggestionCard({ 
  icon, 
  title, 
  description, 
  onClick 
}: { 
  icon: React.ReactNode; 
  title: string; 
  description: string;
  onClick: () => void;
}) {
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
      <div className="font-semibold" style={{ color: '#2F2F27' }}>{title}</div>
      <div className="text-sm opacity-60 mt-1" style={{ color: '#2F2F27' }}>
        {description}
      </div>
    </button>
  );
}

