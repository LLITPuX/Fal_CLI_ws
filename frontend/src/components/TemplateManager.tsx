import { useState } from 'react';
import { useSchemaTemplates } from '../hooks/useSchemaTemplates';

interface TemplateManagerProps {
  onSelect: (schema: string) => void;
  currentSchema: string;
  disabled?: boolean;
}

export const TemplateManager: React.FC<TemplateManagerProps> = ({
  onSelect,
  currentSchema,
  disabled = false,
}) => {
  const {
    templates,
    addTemplate,
    deleteTemplate,
    exportTemplates,
    importTemplates,
  } = useSchemaTemplates();

  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const handleSave = () => {
    if (!currentSchema.trim()) {
      setSaveError('Schema is empty');
      return;
    }

    if (!templateName.trim()) {
      setSaveError('Template name is required');
      return;
    }

    try {
      addTemplate(templateName, currentSchema);
      setTemplateName('');
      setShowSaveDialog(false);
      setSaveError(null);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save');
    }
  };

  const handleExport = () => {
    const json = exportTemplates();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gemini-schema-templates-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        importTemplates(content);
        setImportError(null);
      } catch (error) {
        setImportError(error instanceof Error ? error.message : 'Failed to import');
      }
    };
    reader.readAsText(file);

    // Reset input
    event.target.value = '';
  };

  return (
    <div className="template-manager">
      <div className="template-header">
        <h4>Збережені шаблони</h4>
        <div className="template-actions">
          <button
            type="button"
            onClick={() => setShowSaveDialog(true)}
            className="action-btn"
            disabled={disabled || !currentSchema.trim()}
            title="Зберегти поточну схему"
          >
            💾 Зберегти
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="action-btn"
            disabled={templates.length === 0}
            title="Експортувати всі шаблони"
          >
            📤 Експорт
          </button>
          <label className="action-btn" title="Імпортувати шаблони">
            📥 Імпорт
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>

      {importError && (
        <div className="template-error">
          <span className="error-icon">⚠️</span>
          <span>{importError}</span>
        </div>
      )}

      {showSaveDialog && (
        <div className="save-dialog">
          <input
            type="text"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            placeholder="Назва шаблону..."
            className="template-name-input"
            autoFocus
          />
          <div className="dialog-actions">
            <button
              type="button"
              onClick={handleSave}
              className="save-btn"
            >
              Зберегти
            </button>
            <button
              type="button"
              onClick={() => {
                setShowSaveDialog(false);
                setTemplateName('');
                setSaveError(null);
              }}
              className="cancel-btn"
            >
              Скасувати
            </button>
          </div>
          {saveError && (
            <div className="save-error">{saveError}</div>
          )}
        </div>
      )}

      {templates.length > 0 ? (
        <div className="templates-list">
          {templates.map((template) => (
            <div key={template.id} className="template-item">
              <div className="template-info">
                <span className="template-name">{template.name}</span>
                <span className="template-date">
                  {new Date(template.createdAt).toLocaleDateString('uk-UA')}
                </span>
              </div>
              <div className="template-item-actions">
                <button
                  type="button"
                  onClick={() => onSelect(template.schema)}
                  className="load-btn"
                  disabled={disabled}
                  title="Завантажити цей шаблон"
                >
                  ↓ Завантажити
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (confirm(`Видалити шаблон "${template.name}"?`)) {
                      deleteTemplate(template.id);
                    }
                  }}
                  className="delete-btn"
                  title="Видалити шаблон"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="no-templates">Збережених шаблонів поки немає</p>
      )}
    </div>
  );
};

