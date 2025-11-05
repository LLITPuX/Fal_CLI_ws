import { useState, useRef, useEffect } from 'react';
import { Shield } from 'lucide-react';
import * as chatApi from '../services/chat-api';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [inputValue, setInputValue] = useState('');
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
        setError('Failed to initialize chat session');
      }
    };
    initSession();
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !sessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Send to backend (Писарь will record it)
      await chatApi.sendMessage(inputValue, sessionId, 'user');

      // Simulate assistant response for now (Phase 1 - only Clerk)
      setTimeout(async () => {
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: 'Дякую за ваше повідомлення! Писарь успішно записав його в граф знань. ' +
                   'В Phase 2 (Підсвідомість) та Phase 3 (Оркестратор) я зможу відповідати на основі контексту.',
          role: 'assistant',
          timestamp: new Date(),
        };

        // Record assistant message too
        await chatApi.sendMessage(aiMessage.content, sessionId, 'assistant');

        setMessages((prev) => [...prev, aiMessage]);
        setIsTyping(false);
      }, 1000);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div 
      className="min-h-screen relative"
      style={{
        backgroundColor: '#F3EDDC',
      }}
    >
      <div className="max-w-5xl mx-auto h-screen flex flex-col">
        {/* Header */}
        <div className="p-6 border-b-2" style={{ borderColor: '#2F2F27' }}>
          <div className="flex items-center gap-3">
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center border-2"
              style={{ 
                backgroundColor: '#FFD700',
                borderColor: '#0057B7',
              }}
            >
              <Shield className="w-6 h-6" style={{ color: '#0057B7' }} />
            </div>
            <div>
              <h1 className="text-2xl font-bold" style={{ color: '#2F2F27' }}>
                Cybersich AI
              </h1>
              <p className="text-sm opacity-60" style={{ color: '#2F2F27' }}>
                Писарь Agent • Phase 1 MVP
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-100 border-2 border-red-500 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <Shield className="w-16 h-16 mx-auto mb-4" style={{ color: '#0057B7' }} />
                <h2 className="text-xl font-semibold mb-2" style={{ color: '#2F2F27' }}>
                  Вітаю в Cybersich Chat!
                </h2>
                <p className="text-sm opacity-60" style={{ color: '#2F2F27' }}>
                  Писарь записує всі повідомлення в граф знань
                </p>
              </div>
            )}

            {messages.map((message) => (
              <div key={message.id} className="flex gap-3">
                <div 
                  className="w-10 h-10 rounded-full flex items-center justify-center border-2 flex-shrink-0"
                  style={{ 
                    backgroundColor: message.role === 'user' ? '#2F2F27' : '#FFD700',
                    borderColor: message.role === 'user' ? '#2F2F27' : '#0057B7',
                  }}
                >
                  {message.role === 'assistant' ? (
                    <Shield className="w-5 h-5" style={{ color: '#0057B7' }} />
                  ) : (
                    <span className="text-sm font-bold" style={{ color: '#F3EDDC' }}>U</span>
                  )}
                </div>
                <div 
                  className="rounded-2xl rounded-tl-sm px-5 py-3 max-w-2xl"
                  style={{ 
                    backgroundColor: message.role === 'user' ? '#2F2F27' : '#FFFFFF',
                    color: message.role === 'user' ? '#F3EDDC' : '#2F2F27',
                  }}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
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
                  style={{ backgroundColor: '#FFFFFF', color: '#2F2F27' }}
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
        <div className="border-t-2 p-4" style={{ borderColor: '#2F2F27' }}>
          <div className="max-w-3xl mx-auto flex gap-2">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Напишіть повідомлення..."
              className="flex-1 px-4 py-3 rounded-xl border-2 resize-none"
              style={{
                backgroundColor: '#FFFFFF',
                borderColor: '#2F2F27',
                color: '#2F2F27',
                minHeight: '56px',
                maxHeight: '200px',
              }}
              rows={1}
              disabled={!sessionId}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || !sessionId}
              className="px-6 py-3 rounded-xl font-semibold border-2 transition-opacity disabled:opacity-50"
              style={{
                backgroundColor: '#0057B7',
                borderColor: '#0057B7',
                color: '#FFFFFF',
              }}
            >
              Відправити
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

