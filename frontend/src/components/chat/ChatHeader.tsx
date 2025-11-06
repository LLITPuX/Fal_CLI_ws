import { Shield } from 'lucide-react';

export function ChatHeader() {
  return (
    <header 
      className="border-b-2 px-6 py-4"
      style={{ 
        borderColor: '#2F2F27',
        backgroundColor: '#F3EDDC',
      }}
    >
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div 
            className="w-12 h-12 rounded-full flex items-center justify-center border-2"
            style={{ 
              backgroundColor: '#FFD700',
              borderColor: '#0057B7',
            }}
          >
            <Shield className="w-7 h-7" style={{ color: '#0057B7' }} />
          </div>
          <div>
            <div 
              className="tracking-wider"
              style={{ 
                color: '#2F2F27',
                fontFamily: 'serif',
              }}
            >
              Cybersich
            </div>
            <div 
              className="opacity-70"
              style={{ color: '#2F2F27' }}
            >
              AI Помічник
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}