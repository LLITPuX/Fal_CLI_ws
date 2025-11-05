/**
 * Template Manager component for managing all node templates
 */

import { useState, useEffect, useRef } from 'react';
import type { NodeTemplate } from '../../types/templates';
import { templateApi } from '../../services/template-api';
import { TemplateEditor } from './TemplateEditor';
import '../../styles/TemplateManager.css';

export const TemplateManager = () => {
  const [templates, setTemplates] = useState<NodeTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editingTemplate, setEditingTemplate] = useState<NodeTemplate | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const templateList = await templateApi.getTemplates();
      setTemplates(templateList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setEditingTemplate(null);
    setShowEditor(true);
  };

  const handleEditTemplate = (template: NodeTemplate) => {
    setEditingTemplate(template);
    setShowEditor(true);
  };

  const handleDeleteTemplate = async (template: NodeTemplate) => {
    if (!confirm(`Are you sure you want to delete template "${template.label}"?`)) {
      return;
    }

    try {
      await templateApi.deleteTemplate(template.id);
      showSuccess(`Template "${template.label}" deleted successfully`);
      loadTemplates();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete template');
    }
  };

  const handleMigrateNodes = async (template: NodeTemplate) => {
    if (!confirm(
      `Migrate all existing nodes with label "${template.label}"?\n\n` +
      `This will add new template fields to existing nodes.`
    )) {
      return;
    }

    try {
      const result = await templateApi.migrateNodes({
        templateId: template.id,
        applyDefaults: true,
      });
      
      showSuccess(
        `Migration completed: ${result.nodesUpdated} node(s) updated, ` +
        `${result.fieldsAdded.length} field(s) added`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to migrate nodes');
    }
  };

  const handleExportAll = async () => {
    try {
      await templateApi.downloadTemplatesFile();
      showSuccess('All templates exported successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export templates');
    }
  };

  const handleExportSingle = async (template: NodeTemplate) => {
    try {
      await templateApi.downloadSingleTemplate(template);
      showSuccess(`Template "${template.label}" exported successfully`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export template');
    }
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleImportFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const result = await templateApi.uploadTemplatesFile(file, false);
      
      showSuccess(
        `Import completed: ${result.imported} imported, ${result.skipped} skipped` +
        (result.errors.length > 0 ? `, ${result.errors.length} errors` : '')
      );
      
      if (result.errors.length > 0) {
        console.error('Import errors:', result.errors);
      }
      
      loadTemplates();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import templates');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleEditorSave = () => {
    showSuccess(editingTemplate ? 'Template updated successfully' : 'Template created successfully');
    loadTemplates();
  };

  const showSuccess = (message: string) => {
    setSuccess(message);
    setTimeout(() => setSuccess(null), 5000);
  };

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner"></div>
        <p>Loading templates...</p>
      </div>
    );
  }

  return (
    <div className="template-manager">
      <div className="template-manager-header">
        <h2 className="template-manager-title">📋 Node Templates</h2>
        
        <div className="template-manager-actions">
          <button onClick={handleCreateTemplate} className="btn-primary">
            ➕ Create Template
          </button>
          <button onClick={handleExportAll} className="btn-secondary">
            📥 Export All
          </button>
          <div className="file-input-wrapper">
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleImportFile}
              id="import-file-input"
            />
            <label htmlFor="import-file-input" className="file-input-label" onClick={handleImportClick}>
              📤 Import
            </label>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          ❌ {error}
          <button 
            onClick={() => setError(null)}
            style={{ 
              float: 'right', 
              background: 'none', 
              border: 'none', 
              color: 'inherit', 
              cursor: 'pointer',
              fontSize: '1.2rem'
            }}
          >
            ×
          </button>
        </div>
      )}

      {success && (
        <div className="success-banner">
          ✓ {success}
          <button 
            onClick={() => setSuccess(null)}
            style={{ 
              float: 'right', 
              background: 'none', 
              border: 'none', 
              color: 'inherit', 
              cursor: 'pointer',
              fontSize: '1.2rem'
            }}
          >
            ×
          </button>
        </div>
      )}

      {templates.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📭</div>
          <h3 className="empty-state-title">No Templates Yet</h3>
          <p className="empty-state-description">
            Create your first template to get started with structured node creation.
          </p>
          <button onClick={handleCreateTemplate} className="btn-primary">
            ➕ Create Your First Template
          </button>
        </div>
      ) : (
        <div className="template-list">
          {templates.map((template) => (
            <div key={template.id} className="template-card">
              <div className="template-card-header">
                {template.icon && (
                  <div className="template-card-icon">{template.icon}</div>
                )}
                <div className="template-card-info">
                  <div className="template-card-label">{template.label}</div>
                  <div className="template-card-description">
                    {template.description}
                  </div>
                </div>
              </div>

              <div className="template-card-meta">
                <div className="template-card-meta-item">
                  📊 {template.fields.length} field{template.fields.length !== 1 ? 's' : ''}
                </div>
                <div className="template-card-meta-item">
                  🕐 Updated {new Date(template.updatedAt).toLocaleDateString()}
                </div>
              </div>

              <div className="template-card-actions">
                <button
                  onClick={() => handleEditTemplate(template)}
                  className="btn-small"
                >
                  ✏️ Edit
                </button>
                <button
                  onClick={() => handleExportSingle(template)}
                  className="btn-small"
                  title="Export this template"
                >
                  📥 Export
                </button>
                <button
                  onClick={() => handleMigrateNodes(template)}
                  className="btn-small"
                  title="Migrate existing nodes"
                >
                  🔄 Migrate
                </button>
                <button
                  onClick={() => handleDeleteTemplate(template)}
                  className="btn-small danger"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showEditor && (
        <TemplateEditor
          template={editingTemplate || undefined}
          onClose={() => {
            setShowEditor(false);
            setEditingTemplate(null);
          }}
          onSave={handleEditorSave}
        />
      )}
    </div>
  );
};

