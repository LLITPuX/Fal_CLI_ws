/**
 * Template Editor component for creating and editing node templates
 */

import { useState, useEffect } from 'react';
import type { NodeTemplate, TemplateField, FieldType, CreateTemplateRequest, UpdateTemplateRequest } from '../../types/templates';
import { templateApi } from '../../services/template-api';
import '../../styles/TemplateEditor.css';

interface TemplateEditorProps {
  template?: NodeTemplate;
  onClose: () => void;
  onSave: () => void;
}

export const TemplateEditor = ({ template, onClose, onSave }: TemplateEditorProps) => {
  const [label, setLabel] = useState('');
  const [icon, setIcon] = useState('');
  const [description, setDescription] = useState('');
  const [fields, setFields] = useState<TemplateField[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditMode = !!template;

  useEffect(() => {
    if (template) {
      setLabel(template.label);
      setIcon(template.icon || '');
      setDescription(template.description);
      setFields(template.fields);
    }
  }, [template]);

  const addField = () => {
    const newField: TemplateField = {
      id: `field-${Date.now()}`,
      name: '',
      type: 'text',
      label: '',
      required: false,
      placeholder: '',
      enumValues: undefined,
    };
    setFields([...fields, newField]);
  };

  const removeField = (fieldId: string) => {
    setFields(fields.filter((f) => f.id !== fieldId));
  };

  const updateField = (fieldId: string, updates: Partial<TemplateField>) => {
    setFields(fields.map((f) => {
      if (f.id === fieldId) {
        const updated = { ...f, ...updates };
        // Initialize enumValues array when type changes to enum
        if (updates.type === 'enum' && !updated.enumValues) {
          updated.enumValues = [''];
        }
        // Clear enumValues when type changes from enum to something else
        if (updates.type && updates.type !== 'enum' && f.type === 'enum') {
          updated.enumValues = undefined;
        }
        return updated;
      }
      return f;
    }));
  };

  const addEnumValue = (fieldId: string) => {
    setFields(fields.map((f) => {
      if (f.id === fieldId) {
        return {
          ...f,
          enumValues: [...(f.enumValues || []), ''],
        };
      }
      return f;
    }));
  };

  const updateEnumValue = (fieldId: string, index: number, value: string) => {
    setFields(fields.map((f) => {
      if (f.id === fieldId && f.enumValues) {
        const newValues = [...f.enumValues];
        newValues[index] = value;
        return { ...f, enumValues: newValues };
      }
      return f;
    }));
  };

  const removeEnumValue = (fieldId: string, index: number) => {
    setFields(fields.map((f) => {
      if (f.id === fieldId && f.enumValues) {
        return {
          ...f,
          enumValues: f.enumValues.filter((_, i) => i !== index),
        };
      }
      return f;
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!label.trim()) {
      setError('Label is required');
      return;
    }

    if (!description.trim() || description.trim().length < 10) {
      setError('Description must be at least 10 characters');
      return;
    }

    if (fields.length === 0) {
      setError('At least one field is required');
      return;
    }

    // Validate and clean fields
    const cleanedFields = fields.map(field => {
      // Filter out empty enum values
      if (field.type === 'enum' && field.enumValues) {
        return {
          ...field,
          enumValues: field.enumValues.filter(v => v.trim() !== '')
        };
      }
      return field;
    });

    for (const field of cleanedFields) {
      if (!field.name.trim()) {
        setError(`Field name is required for all fields`);
        return;
      }
      if (!field.label.trim()) {
        setError(`Field label is required for field "${field.name}"`);
        return;
      }
      if (field.type === 'enum' && (!field.enumValues || field.enumValues.length === 0)) {
        setError(`Enum field "${field.name}" must have at least one value`);
        return;
      }
    }

    setIsLoading(true);

    try {
      if (isEditMode && template) {
        // Update existing template
        const request: UpdateTemplateRequest = {
          icon: icon || undefined,
          description: description.trim(),
          fields: cleanedFields,
        };
        await templateApi.updateTemplate(template.id, request);
      } else {
        // Create new template
        const request: CreateTemplateRequest = {
          label: label.trim(),
          icon: icon || undefined,
          description: description.trim(),
          fields: cleanedFields,
        };
        await templateApi.createTemplate(request);
      }

      onSave();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save template');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">
            {isEditMode ? '✏️ Edit Template' : '➕ Create Template'}
          </h2>
          <button type="button" onClick={onClose} className="modal-close">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div className="error-banner" style={{ marginBottom: '1rem' }}>
                {error}
              </div>
            )}

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="template-label">
                  Label *
                </label>
                <input
                  id="template-label"
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="Person, Company, Event..."
                  disabled={isLoading || isEditMode}
                  required
                  className="field-input"
                />
                {isEditMode && (
                  <small style={{ color: 'var(--text-secondary)' }}>
                    Label cannot be changed after creation
                  </small>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="template-icon">
                  Icon
                </label>
                <input
                  id="template-icon"
                  type="text"
                  value={icon}
                  onChange={(e) => setIcon(e.target.value)}
                  placeholder="📦 👤 🏢..."
                  disabled={isLoading}
                  className="field-input"
                  maxLength={2}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="template-description">
                Description *
              </label>
              <textarea
                id="template-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the purpose of this template..."
                disabled={isLoading}
                required
                className="field-textarea"
                rows={3}
              />
              <small style={{ color: 'var(--text-secondary)' }}>
                Minimum 10 characters
              </small>
            </div>

            <div className="field-designer">
              <div className="field-designer-header">
                <div className="field-designer-title">Template Fields</div>
                <button
                  type="button"
                  onClick={addField}
                  className="btn-add-field"
                  disabled={isLoading}
                  style={{ width: 'auto', padding: '0.5rem 1rem' }}
                >
                  ➕ Add Field
                </button>
              </div>

              {fields.length === 0 && (
                <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
                  No fields yet. Click "Add Field" to create one.
                </p>
              )}

              <div className="field-designer-list">
                {fields.map((field, index) => (
                  <div key={field.id} className="field-designer-item">
                    <div className="field-designer-item-header">
                      <div className="field-designer-item-title">
                        Field {index + 1}
                      </div>
                      <button
                        type="button"
                        onClick={() => removeField(field.id)}
                        className="btn-icon danger"
                        title="Remove field"
                      >
                        🗑️
                      </button>
                    </div>

                    <div className="field-designer-item-body">
                      <div className="form-group">
                        <label>Name (key) *</label>
                        <input
                          type="text"
                          value={field.name}
                          onChange={(e) => updateField(field.id, { name: e.target.value })}
                          placeholder="field_name"
                          className="field-input"
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label>Type *</label>
                        <select
                          value={field.type}
                          onChange={(e) => updateField(field.id, { type: e.target.value as FieldType })}
                          className="field-select"
                          required
                        >
                          <option value="text">Text</option>
                          <option value="longtext">Long Text</option>
                          <option value="number">Number</option>
                          <option value="boolean">Boolean</option>
                          <option value="enum">Enum (dropdown)</option>
                          <option value="date">Date</option>
                          <option value="url">URL</option>
                          <option value="email">Email</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label>Label *</label>
                        <input
                          type="text"
                          value={field.label}
                          onChange={(e) => updateField(field.id, { label: e.target.value })}
                          placeholder="Display label"
                          className="field-input"
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label>Placeholder</label>
                        <input
                          type="text"
                          value={field.placeholder || ''}
                          onChange={(e) => updateField(field.id, { placeholder: e.target.value })}
                          placeholder="Optional placeholder"
                          className="field-input"
                        />
                      </div>

                      <div className="form-group field-designer-item-body-full">
                        <label className="checkbox-label">
                          <input
                            type="checkbox"
                            checked={field.required}
                            onChange={(e) => updateField(field.id, { required: e.target.checked })}
                          />
                          <span>Required field</span>
                        </label>
                      </div>

                      {field.type === 'enum' && (
                        <div className="form-group field-designer-item-body-full">
                          <label>Enum Values *</label>
                          <div className="enum-values-editor">
                            {(field.enumValues || []).map((value, valueIndex) => (
                              <div key={valueIndex} className="enum-value-item">
                                <input
                                  type="text"
                                  value={value}
                                  onChange={(e) => updateEnumValue(field.id, valueIndex, e.target.value)}
                                  placeholder={`Value ${valueIndex + 1}`}
                                  className="field-input enum-value-input"
                                  required
                                />
                                <button
                                  type="button"
                                  onClick={() => removeEnumValue(field.id, valueIndex)}
                                  className="btn-remove-enum"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                            <button
                              type="button"
                              onClick={() => addEnumValue(field.id)}
                              className="btn-add-enum"
                            >
                              + Add Value
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : isEditMode ? 'Update Template' : 'Create Template'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

