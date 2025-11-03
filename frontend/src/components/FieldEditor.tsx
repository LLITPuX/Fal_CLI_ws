import { useState, useEffect } from 'react';
import type { SchemaField, FieldType } from '../types/schema';
import { FIELD_TYPE_LABELS, FIELD_TYPE_EXAMPLES } from '../types/schema';

interface FieldEditorProps {
  mode: 'create' | 'edit';
  field?: SchemaField;
  onSave: (field: SchemaField) => void;
  onCancel: () => void;
  existingNames?: string[];
}

export const FieldEditor: React.FC<FieldEditorProps> = ({
  mode,
  field,
  onSave,
  onCancel,
  existingNames = [],
}) => {
  const [name, setName] = useState(field?.name || '');
  const [type, setType] = useState<FieldType>(field?.type || 'string');
  const [description, setDescription] = useState(field?.description || '');
  const [required, setRequired] = useState(field?.required || false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (field) {
      setName(field.name);
      setType(field.type);
      setDescription(field.description);
      setRequired(field.required || false);
    }
  }, [field]);

  const validate = (): boolean => {
    // Check name
    if (!name.trim()) {
      setError('Назва поля обов\'язкова');
      return false;
    }

    // Check for invalid characters
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) {
      setError('Назва має містити лише латинські літери, цифри та підкреслення');
      return false;
    }

    // Check for duplicate names (except when editing same field)
    if (existingNames.includes(name) && name !== field?.name) {
      setError('Поле з такою назвою вже існує');
      return false;
    }

    setError(null);
    return true;
  };

  const handleSave = () => {
    if (!validate()) return;

    const savedField: SchemaField = {
      id: field?.id || crypto.randomUUID(),
      name: name.trim(),
      type,
      description: description.trim(),
      required,
      children: field?.children, // Preserve existing children
    };

    onSave(savedField);
  };

  const handleTypeChange = (newType: FieldType) => {
    setType(newType);
    
    // Clear children if switching away from object/array<object>
    if (newType !== 'object' && newType !== 'array<object>') {
      // Note: We don't modify field.children here, parent will handle
    }
  };

  return (
    <div className="field-editor-overlay" onClick={onCancel}>
      <div className="field-editor-modal" onClick={(e) => e.stopPropagation()}>
        <div className="field-editor-header">
          <h3>{mode === 'create' ? 'Додати нове поле' : 'Редагувати поле'}</h3>
          <button
            type="button"
            onClick={onCancel}
            className="field-editor-close"
            title="Закрити"
          >
            ✕
          </button>
        </div>

        <div className="field-editor-body">
          <div className="form-group">
            <label htmlFor="field-name">
              Назва поля <span className="required">*</span>
            </label>
            <input
              id="field-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="title, summary, tags..."
              className="field-editor-input"
              autoFocus
            />
            <p className="help-text">
              Використовуйте латинські літери, цифри та підкреслення
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="field-type">
              Тип даних <span className="required">*</span>
            </label>
            <select
              id="field-type"
              value={type}
              onChange={(e) => handleTypeChange(e.target.value as FieldType)}
              className="field-editor-select"
            >
              {Object.entries(FIELD_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <p className="help-text">
              Приклад: {FIELD_TYPE_EXAMPLES[type]}
            </p>
          </div>

          <div className="form-group">
            <label htmlFor="field-description">Опис</label>
            <textarea
              id="field-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Детальний опис для моделі AI..."
              rows={4}
              className="field-editor-textarea"
            />
            <p className="help-text">
              Допоможе моделі краще зрозуміти, які дані очікуються
            </p>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={required}
                onChange={(e) => setRequired(e.target.checked)}
                className="field-editor-checkbox"
              />
              <span>Обов'язкове поле</span>
            </label>
          </div>

          {error && (
            <div className="field-editor-error">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className="field-editor-footer">
          <button
            type="button"
            onClick={onCancel}
            className="btn-secondary"
          >
            Скасувати
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="btn-primary"
          >
            {mode === 'create' ? 'Додати' : 'Зберегти'}
          </button>
        </div>
      </div>
    </div>
  );
};

