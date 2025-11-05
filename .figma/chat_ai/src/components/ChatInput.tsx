import { useState, KeyboardEvent } from 'react';
import { Send, Paperclip, Mic } from 'lucide-react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';

export function ChatInput({ onSend }: { onSend: (message: string) => void }) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
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
          <Button
            variant="ghost"
            size="icon"
            className="flex-shrink-0"
            style={{ color: '#2F2F27' }}
          >
            <Paperclip className="w-5 h-5" />
          </Button>

          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Напишіть ваше повідомлення..."
            className="flex-1 min-h-[50px] max-h-[200px] border-0 resize-none focus-visible:ring-0 focus-visible:ring-offset-0 p-0"
            style={{ 
              backgroundColor: 'transparent',
              color: '#2F2F27',
            }}
          />

          <div className="flex gap-2 flex-shrink-0">
            <Button
              variant="ghost"
              size="icon"
              style={{ color: '#2F2F27' }}
            >
              <Mic className="w-5 h-5" />
            </Button>
            <Button
              onClick={handleSend}
              disabled={!input.trim()}
              size="icon"
              className="rounded-full"
              style={{
                backgroundColor: input.trim() ? '#0057B7' : '#CCC',
                color: '#FFFFFF',
              }}
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
        </div>
        
        <div 
          className="mt-2 text-center opacity-60"
          style={{ color: '#2F2F27' }}
        >
          Cybersich AI може помилятися. Перевіряйте важливу інформацію.
        </div>
      </div>
    </div>
  );
}
