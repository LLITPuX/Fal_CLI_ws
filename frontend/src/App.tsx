import { useState } from 'react';
import { TextInput } from './components/TextInput';
import { JsonViewer } from './components/JsonViewer';
import { ErrorMessage } from './components/ErrorMessage';
import { apiClient } from './services/api';
import type { LoadingState, StructureRequest } from './types/api';
import './styles/App.css';

function App() {
  const [loadingState, setLoadingState] = useState<LoadingState>({ status: 'idle' });

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

  return (
    <div className="app">
      <header className="app-header">
        <h1>🤖 Gemini Text Structurer</h1>
        <p>Transform unstructured text into structured JSON with performance metrics</p>
      </header>

      <main className="app-main">
        <div className="container">
          <div className="input-section">
            <TextInput
              onSubmit={handleSubmit}
              isLoading={loadingState.status === 'loading'}
            />
          </div>

          <div className="output-section">
            {loadingState.status === 'loading' && (
              <div className="loading-state">
                <div className="spinner-large" />
                <p>Processing your text with Gemini AI...</p>
                <p className="loading-hint">⏱️ This may take up to 5 minutes</p>
                <div className="loading-models">
                  <span>Using: gemini-2.5-flash (optimal for free tier)</span>
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
                  <span>⚡ Powered by gemini-2.5-flash</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by Google Gemini AI · Text Structuring Tool · v2.2.0</p>
      </footer>
    </div>
  );
}

export default App;

