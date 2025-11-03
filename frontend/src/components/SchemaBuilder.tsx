import { useState } from 'react';
import type { VisualSchema, SchemaField } from '../types/schema';
import { FieldCard } from './FieldCard';
import { FieldEditor } from './FieldEditor';
import { visualSchemaToJSON, getDefaultVisualSchema } from '../utils/schemaConverter';

interface SchemaBuilderProps {
  value: VisualSchema;
  onChange: (schema: VisualSchema) => void;
  disabled?: boolean;
}

export const SchemaBuilder: React.FC<SchemaBuilderProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const [showEditor, setShowEditor] = useState(false);
  const [editingField, setEditingField] = useState<SchemaField | undefined>();
  const [editorMode, setEditorMode] = useState<'create' | 'edit'>('create');

  const handleAddField = () => {
    setEditorMode('create');
    setEditingField(undefined);
    setShowEditor(true);
  };

  const handleEditField = (field: SchemaField) => {
    setEditorMode('edit');
    setEditingField(field);
    setShowEditor(true);
  };

  const handleSaveField = (field: SchemaField) => {
    if (editorMode === 'create') {
      // Add new field
      onChange({
        ...value,
        fields: [...value.fields, field],
      });
    } else {
      // Update existing field
      onChange({
        ...value,
        fields: value.fields.map((f) => (f.id === field.id ? field : f)),
      });
    }
    setShowEditor(false);
    setEditingField(undefined);
  };

  const handleDeleteField = (id: string) => {
    onChange({
      ...value,
      fields: value.fields.filter((f) => f.id !== id),
    });
  };

  const handleMoveField = (id: string, direction: 'up' | 'down') => {
    const index = value.fields.findIndex((f) => f.id === id);
    if (index === -1) return;

    const newFields = [...value.fields];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newFields.length) return;

    // Swap
    [newFields[index], newFields[targetIndex]] = [newFields[targetIndex], newFields[index]];

    onChange({
      ...value,
      fields: newFields,
    });
  };

  const handleReset = () => {
    if (confirm('Скинути до дефолтної схеми? Всі поточні зміни будуть втрачені.')) {
      onChange(getDefaultVisualSchema());
    }
  };

  const handleClear = () => {
    if (confirm('Очистити всі поля? Ця дія незворотна.')) {
      onChange({ fields: [] });
    }
  };

  const existingNames = value.fields.map((f) => f.name);

  return (
    <div className="schema-builder">
      <div className="schema-builder-header">
        <div className="schema-builder-title">
          <h4>Конструктор JSON-схеми</h4>
          <span className="field-count">
            {value.fields.length} {value.fields.length === 1 ? 'поле' : 'полів'}
          </span>
        </div>
        <div className="schema-builder-actions">
          <button
            type="button"
            onClick={handleReset}
            className="btn-action"
            disabled={disabled}
            title="Скинути до дефолтної схеми"
          >
            ↺ Дефолт
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="btn-action"
            disabled={disabled || value.fields.length === 0}
            title="Очистити всі поля"
          >
            🗑️ Очистити
          </button>
          <button
            type="button"
            onClick={handleAddField}
            className="btn-add-field"
            disabled={disabled}
          >
            + Додати поле
          </button>
        </div>
      </div>

      {value.fields.length === 0 ? (
        <div className="schema-builder-empty">
          <div className="empty-icon">📝</div>
          <p>Схема порожня</p>
          <p className="empty-hint">
            Натисніть "Додати поле" або "Дефолт" щоб почати
          </p>
        </div>
      ) : (
        <div className="schema-builder-fields">
          {value.fields.map((field, index) => (
            <FieldCard
              key={field.id}
              field={field}
              onEdit={handleEditField}
              onDelete={handleDeleteField}
              onMoveUp={(id) => handleMoveField(id, 'up')}
              onMoveDown={(id) => handleMoveField(id, 'down')}
              canMoveUp={index > 0}
              canMoveDown={index < value.fields.length - 1}
              disabled={disabled}
            />
          ))}
        </div>
      )}

      <div className="schema-builder-footer">
        <details className="schema-preview">
          <summary>Попередній перегляд JSON</summary>
          <pre className="schema-preview-json">
            <code>
              {value.fields.length > 0
                ? visualSchemaToJSON(value)
                : '// Додайте поля для генерації схеми'}
            </code>
          </pre>
        </details>
      </div>

      {showEditor && (
        <FieldEditor
          mode={editorMode}
          field={editingField}
          onSave={handleSaveField}
          onCancel={() => {
            setShowEditor(false);
            setEditingField(undefined);
          }}
          existingNames={editorMode === 'edit' ? existingNames.filter(n => n !== editingField?.name) : existingNames}
        />
      )}
    </div>
  );
};

