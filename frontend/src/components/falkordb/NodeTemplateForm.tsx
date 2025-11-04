/**
 * Form for creating nodes using templates
 */

import { useState, useEffect } from 'react';
import type { CreateNodeRequest } from '../../types/falkordb';
import type { NodeTemplate } from '../../types/templates';
import { templateApi } from '../../services/template-api';
import { TemplateFieldRenderer } from './fields/TemplateFieldRenderer';
import '../../styles/TemplateFields.css';

interface NodeTemplateFormProps {
  onSubmit: (request: CreateNodeRequest) => Promise<void>;
  isLoading: boolean;
  onOpenTemplateEditor?: () => void;
}

export const NodeTemplateForm = ({ 
  onSubmit, 
  isLoading,
  onOpenTemplateEditor 
}: NodeTemplateFormProps) => {
  const [templates, setTemplates] = useState<NodeTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<NodeTemplate | null>(null);
  const [fieldValues, setFieldValues] = useState<Record<string, any>>({});
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, []);

  // Load selected template details
  useEffect(() => {
    if (selectedTemplateId) {
      loadSelectedTemplate(selectedTemplateId);
    } else {
      setSelectedTemplate(null);
      setFieldValues({});
    }
  }, [selectedTemplateId]);

  const loadTemplates = async () => {
    try {
      setLoadingTemplates(true);
      setError(null);
      const templateList = await templateApi.getTemplates();
      setTemplates(templateList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const loadSelectedTemplate = async (templateId: string) => {
    try {
      const template = await templateApi.getTemplate(templateId);
      setSelectedTemplate(template);
      
      // Initialize field values with defaults
      const initialValues: Record<string, any> = {};
      template.fields.forEach((field) => {
        if (field.defaultValue !== undefined && field.defaultValue !== null) {
          initialValues[field.name] = field.defaultValue;
        }
      });
      setFieldValues(initialValues);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load template');
    }
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    setFieldValues((prev) => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedTemplate) {
      alert('Please select a template');
      return;
    }

    // Validate required fields
    for (const field of selectedTemplate.fields) {
      if (field.required && !fieldValues[field.name]) {
        alert(`Field "${field.label}" is required`);
        return;
      }
    }

    // Build properties object
    const properties: Record<string, any> = {};
    selectedTemplate.fields.forEach((field) => {
      const value = fieldValues[field.name];
      if (value !== undefined && value !== null && value !== '') {
        properties[field.name] = value;
      }
    });

    await onSubmit({
      label: selectedTemplate.label,
      properties,
      template_id: selectedTemplate.id,
    });

    // Reset form
    setSelectedTemplateId('');
    setSelectedTemplate(null);
    setFieldValues({});
  };

  return (
    <form onSubmit={handleSubmit} className="falkordb-form">
      <h3>📍 Create Node from Template</h3>

      {error && (
        <div className="error-banner" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div className="form-group">
        <label htmlFor="template-select">
          Select Template *
        </label>
        
        {loadingTemplates ? (
          <div className="loading-indicator">Loading templates...</div>
        ) : templates.length === 0 ? (
          <div className="info-message">
            No templates available. Create a template first.
          </div>
        ) : (
          <select
            id="template-select"
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
            disabled={isLoading}
            required
            className="select-input"
          >
            <option value="">Choose a template...</option>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.icon} {template.label}
              </option>
            ))}
          </select>
        )}

        {selectedTemplate && (
          <p className="field-description" style={{ 
            fontSize: '0.9rem', 
            color: 'var(--text-secondary)',
            marginTop: '0.5rem'
          }}>
            {selectedTemplate.description}
          </p>
        )}
      </div>

      {selectedTemplate && (
        <div className="field-section">
          <div className="field-section-title">
            {selectedTemplate.icon} {selectedTemplate.label} Details
          </div>
          
          {selectedTemplate.fields.map((field) => (
            <TemplateFieldRenderer
              key={field.id}
              field={field}
              value={fieldValues[field.name]}
              onChange={(value) => handleFieldChange(field.name, value)}
              disabled={isLoading}
            />
          ))}
        </div>
      )}

      {onOpenTemplateEditor && (
        <button
          type="button"
          onClick={onOpenTemplateEditor}
          className="btn-secondary"
          disabled={isLoading}
          style={{ marginBottom: '1rem' }}
        >
          ➕ Create New Template
        </button>
      )}

      <button 
        type="submit" 
        disabled={isLoading || !selectedTemplate} 
        className="btn-primary"
      >
        {isLoading ? 'Creating...' : 'Create Node'}
      </button>
    </form>
  );
};

