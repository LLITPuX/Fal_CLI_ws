/**
 * Gemini Text Structurer Page (original functionality)
 * Redesigned with Cossack theme to match ChatPage and GraphVisualizationPage
 */

import { useMemo, useState } from 'react';
import { Sparkles } from 'lucide-react';
import { TextInput } from '../components/TextInput';
import { JsonViewer } from '../components/JsonViewer';
import { ErrorMessage } from '../components/ErrorMessage';
import { CybersichHeader } from '../components/CybersichHeader';
import { apiClient } from '../services/api';
import type { LoadingState, StructureRequest } from '../types/api';

// Background image - той самий що в ChatPage
const backgroundImage = '/2d76d3ed895b0324df0b5302921cd6c50e5b7a9e.png';

// Козацька палітра
const COLORS = {
  beige: '#F3EDDC',
  darkBrown: '#2F2F27',
  gold: '#FFD700',
  blue: '#0057B7',
};

const MODEL_HINTS: Record<string, string> = {
  'gemini-2.5-flash': ' (optimal for free tier)',
  'gemini-2.5-pro': ' (paid tier only - 2 RPM)',
};

export const GeminiPage = () => {
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

  return (
    <div 
      className="min-h-screen relative"
      style={{
        backgroundImage: `linear-gradient(rgba(243, 237, 220, 0.75), rgba(243, 237, 220, 0.75)), url(${backgroundImage})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <CybersichHeader 
        title="Cybersich" 
        subtitle="AI Помічник · Text Structurer" 
      />
      
      <div className="max-w-7xl mx-auto h-[calc(100vh-80px)] flex flex-col gap-6 pt-6">

        <main className="flex-1 overflow-hidden min-h-0 px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
            {/* Input Section */}
            <div 
              className="rounded-2xl overflow-hidden border-4 shadow-2xl"
              style={{
                backgroundColor: COLORS.beige,
                borderColor: COLORS.darkBrown,
              }}
            >
              <TextInput
                onSubmit={handleSubmit}
                isLoading={loadingState.status === 'loading'}
                model={selectedModel}
                onModelChange={setSelectedModel}
              />
            </div>

            {/* Output Section */}
            <div 
              className="rounded-2xl overflow-hidden border-4 shadow-2xl"
              style={{
                backgroundColor: COLORS.beige,
                borderColor: COLORS.darkBrown,
              }}
            >
              {loadingState.status === 'loading' && (
                <div className="h-full flex flex-col items-center justify-center p-8">
                  <div 
                    className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mb-4"
                    style={{ borderColor: COLORS.blue, borderTopColor: 'transparent' }}
                  />
                  <p 
                    className="text-lg font-semibold mb-2"
                    style={{ color: COLORS.darkBrown }}
                  >
                    Processing your text with Gemini AI...
                  </p>
                  <p 
                    className="text-sm mb-4"
                    style={{ color: COLORS.darkBrown, opacity: 0.7 }}
                  >
                    ⏱️ This may take up to 5 minutes
                  </p>
                  <div 
                    className="px-4 py-2 rounded-lg"
                    style={{ backgroundColor: COLORS.gold }}
                  >
                    <span 
                      className="text-sm font-medium"
                      style={{ color: COLORS.blue }}
                    >
                      Using: {selectedModel}
                      {MODEL_HINTS[selectedModel] ?? ''}
                    </span>
                  </div>
                </div>
              )}

              {loadingState.status === 'error' && (
                <div className="p-6">
                  <ErrorMessage message={loadingState.error} onDismiss={handleDismissError} />
                </div>
              )}

              {loadingState.status === 'success' && (
                <div className="h-full overflow-y-auto">
                  <JsonViewer data={loadingState.data} />
                </div>
              )}

              {loadingState.status === 'idle' && (
                <div className="h-full flex flex-col items-center justify-center p-8 text-center">
                  <div 
                    className="w-20 h-20 rounded-full flex items-center justify-center mb-6 border-4"
                    style={{ 
                      backgroundColor: COLORS.gold,
                      borderColor: COLORS.blue,
                    }}
                  >
                    <Sparkles className="w-10 h-10" style={{ color: COLORS.blue }} />
                  </div>
                  <h3 
                    className="text-2xl font-bold mb-4"
                    style={{ color: COLORS.darkBrown }}
                  >
                    Ready to structure your text
                  </h3>
                  <p 
                    className="text-base mb-6"
                    style={{ color: COLORS.darkBrown, opacity: 0.8 }}
                  >
                    Enter unstructured text to transform it into structured JSON
                  </p>
                  <div 
                    className="px-6 py-3 rounded-lg"
                    style={{ backgroundColor: COLORS.gold }}
                  >
                    <span 
                      className="text-sm font-medium"
                      style={{ color: COLORS.blue }}
                    >
                      ⚡ Powered by {selectedModel}
                      {MODEL_HINTS[selectedModel] ?? ''}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>

        {/* Footer - Cossack Wisdom */}
        <footer className="px-6 pb-6">
          <div 
            className="rounded-2xl p-4 text-center border-2"
            style={{
              backgroundColor: COLORS.darkBrown,
              borderColor: COLORS.gold,
              color: COLORS.beige,
            }}
          >
            <p className="flex items-center justify-center gap-2 text-sm">
              <Sparkles className="w-4 h-4" style={{ color: COLORS.gold }} />
              <span>Powered by Google Gemini AI & FalkorDB · Cybersich v2.3.0</span>
              <Sparkles className="w-4 h-4" style={{ color: COLORS.gold }} />
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};
