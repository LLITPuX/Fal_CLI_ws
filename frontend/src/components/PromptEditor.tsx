import { useState } from 'react';

interface PromptEditorProps {
  value: string;
  onChange: (value: string) => void;
  onReset: () => void;
  disabled?: boolean;
}

const DEFAULT_SCHEMA = `{
  "title": "string - A concise, descriptive title extracted from the text",
  "date_iso": "YYYY-MM-DD - Publication or creation date in ISO 8601 format. Use today's date if not found",
  "summary": "string - A comprehensive 2-3 sentence summary capturing the main ideas",
  "tags": ["array of strings - Keywords or topics (3-7 tags). Be specific and relevant"],
  "sections": [
    {
      "name": "string - Section heading or topic name",
      "content": "string - Full content of this section, preserving important details"
    }
  ]
}`;

export const PromptEditor: React.FC<PromptEditorProps> = ({
  value,
  onChange,
  onReset,
  disabled = false,
}) => {
  const [jsonError, setJsonError] = useState<string | null>(null);

  const handleChange = (newValue: string) => {
    onChange(newValue);

    // Validate JSON if not empty
    if (newValue.trim()) {
      try {
        JSON.parse(newValue);
        setJsonError(null);
      } catch (e) {
        setJsonError(e instanceof Error ? e.message : 'Invalid JSON');
      }
    } else {
      setJsonError(null);
    }
  };

  const handleResetClick = () => {
    onReset();
    setJsonError(null);
  };

  return (
    <div className="prompt-editor">
      <div className="editor-header">
        <label htmlFor="schema-editor">
          Користувацька JSON-схема
          <span className="optional">(опційно)</span>
        </label>
        <button
          type="button"
          onClick={handleResetClick}
          className="reset-btn"
          disabled={disabled}
        >
          ↺ Скинути до дефолту
        </button>
      </div>

      <textarea
        id="schema-editor"
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={`Введіть власну JSON-схему або залиште порожнім для дефолтної...\n\nПриклад:\n${DEFAULT_SCHEMA}`}
        rows={18}
        className={`schema-editor ${jsonError ? 'error' : ''}`}
        disabled={disabled}
        spellCheck={false}
      />

      {jsonError && (
        <div className="editor-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{jsonError}</span>
        </div>
      )}

      <div className="editor-hints">
        <p className="hint">
          💡 <strong>Порада:</strong> Додайте описи після назв полів, щоб направити модель
        </p>
        <p className="hint">
          📝 Модель використає цю схему для структурування тексту. Залишіть порожнім для стандартної схеми.
        </p>
      </div>
    </div>
  );
};

