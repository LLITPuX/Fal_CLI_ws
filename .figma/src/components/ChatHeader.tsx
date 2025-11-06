import React from 'react';
import { Shield, Menu, Settings } from 'lucide-react';
import { Button } from './ui/button';
import designGuide from 'figma:asset/da9550dcbe65c2aac03f4ad82653151f4edb368e.png';

export function ChatHeader(): JSX.Element {
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
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full"
            style={{ color: '#2F2F27' }}
          >
            <Settings className="w-5 h-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-full"
            style={{ color: '#2F2F27' }}
          >
            <Menu className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </header>
  );
}