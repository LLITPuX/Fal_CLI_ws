import { useState } from 'react';
import type { StructureRequest } from '../types/api';

interface TextInputProps {
  onSubmit: (request: StructureRequest) => Promise<void>;
  isLoading: boolean;
  model: string;
  onModelChange: (model: string) => void;
}

export const TextInput: React.FC<TextInputProps> = ({
  onSubmit,
  isLoading,
  model,
  onModelChange,
}) => {
  const [text, setText] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    await onSubmit({
      text: text.trim(),
      model,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="text-input-form">
      <div className="form-group">
        <label htmlFor="text-input">
          Unstructured Text
          <span className="required">*</span>
        </label>
        <textarea
          id="text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter your unstructured text here..."
          rows={12}
          disabled={isLoading}
          required
        />
        <p className="help-text">
          Paste any unstructured text. AI will extract title, date, summary, tags, and sections.
        </p>
      </div>

      <div className="advanced-toggle">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="toggle-btn"
        >
          {showAdvanced ? '▼' : '▶'} Advanced Settings
        </button>
      </div>

      {showAdvanced && (
        <div className="advanced-settings">
          <div className="form-group">
            <label htmlFor="model-select">Gemini Model</label>
            <select
              id="model-select"
              value={model}
              onChange={(e) => onModelChange(e.target.value)}
              disabled={isLoading}
            >
              <option value="gemini-2.5-flash">gemini-2.5-flash (Recommended - 15 RPM)</option>
              <option value="gemini-2.5-pro">gemini-2.5-pro (Paid tier only - 2 RPM)</option>
            </select>
          </div>
        </div>
      )}

      <button type="submit" className="submit-btn" disabled={isLoading || !text.trim()}>
        {isLoading ? (
          <>
            <span className="spinner" />
            Processing...
          </>
        ) : (
          'Structure Text'
        )}
      </button>
    </form>
  );
};

