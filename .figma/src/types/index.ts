/**
 * Общие типы для Cybersich AI Chat
 */

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface SuggestionCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}

export interface ChatMessageProps {
  message: Message;
}

export interface ChatInputProps {
  onSend: (message: string) => void;
}
