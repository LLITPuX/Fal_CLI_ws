/**
 * Gemini Text Structurer Page (original functionality)
 */

import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TextInput } from '../components/TextInput';
import { JsonViewer } from '../components/JsonViewer';
import { ErrorMessage } from '../components/ErrorMessage';
import { apiClient } from '../services/api';
import type { LoadingState, StructureRequest } from '../types/api';

const MODEL_HINTS: Record<string, string> = {
  'gemini-2.5-flash': ' (optimal for free tier)',
  'gemini-2.5-pro': ' (paid tier only - 2 RPM)',
};

export const GeminiPage = () => {
  const navigate = useNavigate();
  const defaultModel = useMemo(
    () => (import.meta.env.VITE_GEMINI_MODEL as string | undefined) ?? 'gemini-2.5-flash',
    []
  );
  const [loadingState, setLoadingState] = useState<LoadingState>({ status: 'idle' });
  const [selectedModel, setSelectedModel] = useState<string>(defaultModel);

  const handleSubmit = async (request: StructureRequest) => {
    setLoadingState({ status: 'loading' });

    try {
      const response = await apiClient.structureText(request);
      setLoadingState({ status: 'success', data: response });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An unexpected error occurred';
      setLoadingState({ status: 'error', error: message });
    }
  };

  const handleDismissError = () => {
    setLoadingState({ status: 'idle' });
  };

  const handleChatClick = () => {
    navigate('/chat');
  };

  return (
    <div className="gemini-page">
      <header className="app-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1>🤖 Gemini Text Structurer</h1>
            <p>Transform unstructured text into structured JSON with performance metrics</p>
          </div>
          <button
            onClick={handleChatClick}
            className="chat-button"
            style={{
              padding: '12px 24px',
              backgroundColor: '#0057B7',
              color: '#FFFFFF',
              border: '2px solid #0057B7',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#FFD700';
              e.currentTarget.style.borderColor = '#FFD700';
              e.currentTarget.style.color = '#0057B7';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#0057B7';
              e.currentTarget.style.borderColor = '#0057B7';
              e.currentTarget.style.color = '#FFFFFF';
            }}
          >
            💬 Cybersich Chat
          </button>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <div className="input-section">
            <TextInput
              onSubmit={handleSubmit}
              isLoading={loadingState.status === 'loading'}
              model={selectedModel}
              onModelChange={setSelectedModel}
            />
          </div>

          <div className="output-section">
            {loadingState.status === 'loading' && (
              <div className="loading-state">
                <div className="spinner-large" />
                <p>Processing your text with Gemini AI...</p>
                <p className="loading-hint">⏱️ This may take up to 5 minutes</p>
                <div className="loading-models">
                  <span>
                    Using: {selectedModel}
                    {MODEL_HINTS[selectedModel] ?? ''}
                  </span>
                </div>
              </div>
            )}

            {loadingState.status === 'error' && (
              <ErrorMessage message={loadingState.error} onDismiss={handleDismissError} />
            )}

            {loadingState.status === 'success' && <JsonViewer data={loadingState.data} />}

            {loadingState.status === 'idle' && (
              <div className="idle-state">
                <div className="idle-icon">📝</div>
                <h3>Ready to structure your text</h3>
                <p>Enter unstructured text to transform it into structured JSON</p>
                <div className="models-list">
                  <span>
                    ⚡ Powered by {selectedModel}
                    {MODEL_HINTS[selectedModel] ?? ''}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

