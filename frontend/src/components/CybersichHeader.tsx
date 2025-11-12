/**
 * Universal Cybersich Header - Cossack style for all pages with navigation
 */

import { Shield, Bot, Network, MessageCircle } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

interface CybersichHeaderProps {
  title?: string;
  subtitle?: string;
}

export function CybersichHeader({ 
  title = "Cybersich",
  subtitle = "AI Помічник" 
}: CybersichHeaderProps) {
  const location = useLocation();

  const navLinks = [
    { path: '/', label: 'Text Structurer', icon: Bot },
    { path: '/falkordb', label: 'Граф Січі', icon: Network },
    { path: '/chat', label: 'Chat', icon: MessageCircle },
  ];

  return (
    <header 
      className="w-full border-b-2 py-4"
      style={{ 
        borderColor: '#2F2F27',
        backgroundColor: '#F3EDDC',
      }}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        {/* Logo and Title */}
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
              className="text-2xl font-bold tracking-wider"
              style={{ 
                color: '#2F2F27',
                fontFamily: 'serif',
              }}
            >
              {title}
            </div>
            <div 
              className="text-sm opacity-70"
              style={{ color: '#2F2F27' }}
            >
              {subtitle}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-2">
          {navLinks.map(({ path, label, icon: Icon }) => {
            const isActive = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                className="flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 border-2"
                style={{
                  backgroundColor: isActive ? '#0057B7' : 'transparent',
                  borderColor: isActive ? '#0057B7' : '#2F2F27',
                  color: isActive ? '#F3EDDC' : '#2F2F27',
                  fontWeight: isActive ? 'bold' : 'normal',
                }}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

