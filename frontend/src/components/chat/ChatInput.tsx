import { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';

export function ChatInput({ onSend, disabled }: { onSend: (message: string) => void; disabled?: boolean }) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div 
      className="px-6 py-4"
      style={{ 
        backgroundColor: 'transparent',
      }}
    >
      <div className="max-w-4xl mx-auto">
        <div 
          className="flex gap-3 items-end p-3 rounded-2xl border-2"
          style={{ 
            borderColor: '#2F2F27',
            backgroundColor: '#FFFFFF',
          }}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Напишіть ваше повідомлення..."
            disabled={disabled}
            className="flex-1 min-h-[50px] max-h-[200px] border-0 resize-none focus-visible:ring-0 focus-visible:outline-none p-2"
            style={{ 
              backgroundColor: 'transparent',
              color: '#2F2F27',
            }}
          />

          <button
            onClick={handleSend}
            disabled={!input.trim() || disabled}
            className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-colors disabled:opacity-50"
            style={{
              backgroundColor: input.trim() && !disabled ? '#0057B7' : '#CCC',
              color: '#FFFFFF',
            }}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        
        <div 
          className="mt-2 text-xs text-center opacity-60"
          style={{ color: '#2F2F27' }}
        >
          Cybersich AI може помилятися. Перевіряйте важливу інформацію.
        </div>
      </div>
    </div>
  );
}

