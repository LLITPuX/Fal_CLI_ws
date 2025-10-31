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
        <h1>🤖 Gemini Multi-Model Tester</h1>
        <p>Compare all three Gemini models side-by-side with performance metrics</p>
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
                <p>Processing your text with all Gemini models...</p>
                <p className="loading-hint">⏱️ This will take up to 15 minutes (5 min per model)</p>
                <div className="loading-models">
                  <span>Testing: gemini-2.5-pro → gemini-2.5-flash → gemini-2.5-flash-light</span>
                </div>
              </div>
            )}

            {loadingState.status === 'error' && (
              <ErrorMessage message={loadingState.error} onDismiss={handleDismissError} />
            )}

            {loadingState.status === 'success' && <JsonViewer data={loadingState.data} />}

            {loadingState.status === 'idle' && (
              <div className="idle-state">
                <div className="idle-icon">🔬</div>
                <h3>Ready to test Gemini models</h3>
                <p>Enter text to process with all three models sequentially</p>
                <div className="models-list">
                  <span>📊 gemini-2.5-pro</span>
                  <span>⚡ gemini-2.5-flash</span>
                  <span>🚀 gemini-2.5-flash-light</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Powered by Google Gemini AI · Multi-Model Comparison Tool · v2.1.0</p>
      </footer>
    </div>
  );
}

export default App;

