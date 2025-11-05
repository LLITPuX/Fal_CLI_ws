/**
 * Chat API service for Cybersich Chat System
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ChatSession {
  session_id: string;
  created_at: string;
  user_id?: string;
  title?: string;
  status: string;
}

export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  status: string;
}

export interface SendMessageResponse {
  message_id: string;
  session_id: string;
  status: string;
  recorded: boolean;
  error?: string;
}

export interface MessageHistory {
  session_id: string;
  messages: ChatMessage[];
  total: number;
}

/**
 * Create a new chat session
 */
export async function createSession(
  userId?: string,
  title?: string
): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/api/chat/session`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      title: title,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to create session: ${error}`);
  }

  return response.json();
}

/**
 * Send a message in the chat
 */
export async function sendMessage(
  content: string,
  sessionId: string,
  role: 'user' | 'assistant' = 'user'
): Promise<SendMessageResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content,
      session_id: sessionId,
      role,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to send message: ${error}`);
  }

  return response.json();
}

/**
 * Get message history for a session
 */
export async function getHistory(
  sessionId: string,
  limit: number = 50,
  offset: number = 0
): Promise<MessageHistory> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/chat/session/${sessionId}/history?${params}`
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get history: ${error}`);
  }

  return response.json();
}

/**
 * Get session information
 */
export async function getSession(sessionId: string): Promise<ChatSession> {
  const response = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to get session: ${error}`);
  }

  return response.json();
}

