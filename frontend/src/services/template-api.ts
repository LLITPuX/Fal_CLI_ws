/**
 * API client for node templates
 */

import type {
  CreateTemplateRequest,
  NodeTemplate,
  TemplateExportResponse,
  TemplateImportRequest,
  TemplateImportResponse,
  TemplateListResponse,
  TemplateMigrationRequest,
  TemplateMigrationResponse,
  TemplateResponse,
  UpdateTemplateRequest,
} from '../types/templates';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export class TemplateApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get all templates
   */
  async getTemplates(): Promise<NodeTemplate[]> {
    const response = await fetch(`${this.baseUrl}/falkordb/templates`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch templates: ${response.statusText}`);
    }

    const data: TemplateListResponse = await response.json();
    return data.templates;
  }

  /**
   * Get a specific template by ID
   */
  async getTemplate(id: string): Promise<NodeTemplate> {
    const response = await fetch(`${this.baseUrl}/falkordb/templates/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch template: ${response.statusText}`);
    }

    const data: TemplateResponse = await response.json();
    if (!data.template) {
      throw new Error('Template not found');
    }
    return data.template;
  }

  /**
   * Create a new template
   */
  async createTemplate(request: CreateTemplateRequest): Promise<NodeTemplate> {
    const response = await fetch(`${this.baseUrl}/falkordb/templates`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create template: ${response.statusText}`);
    }

    const data: TemplateResponse = await response.json();
    if (!data.template) {
      throw new Error('Failed to create template');
    }
    return data.template;
  }

  /**
   * Update an existing template
   */
  async updateTemplate(id: string, request: UpdateTemplateRequest): Promise<NodeTemplate> {
    const response = await fetch(`${this.baseUrl}/falkordb/templates/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to update template: ${response.statusText}`);
    }

    const data: TemplateResponse = await response.json();
    if (!data.template) {
      throw new Error('Failed to update template');
    }
    return data.template;
  }

  /**
   * Delete a template
   */
  async deleteTemplate(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/falkordb/templates/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to delete template: ${response.statusText}`);
    }
  }

  /**
   * Migrate nodes after template update
   */
  async migrateNodes(request: TemplateMigrationRequest): Promise<TemplateMigrationResponse> {
    const response = await fetch(
      `${this.baseUrl}/falkordb/templates/${request.templateId}/migrate`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ apply_defaults: request.applyDefaults }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to migrate nodes: ${response.statusText}`);
    }

    const data: TemplateMigrationResponse = await response.json();
    return data;
  }

  /**
   * Export all templates as JSON
   */
  async exportTemplates(): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/falkordb/templates/export/all`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to export templates: ${response.statusText}`);
    }

    const data: TemplateExportResponse = await response.json();
    return data.templates;
  }

  /**
   * Import templates from JSON
   */
  async importTemplates(request: TemplateImportRequest): Promise<TemplateImportResponse> {
    const response = await fetch(`${this.baseUrl}/falkordb/templates/import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to import templates: ${response.statusText}`);
    }

    const data: TemplateImportResponse = await response.json();
    return data;
  }

  /**
   * Download templates as JSON file
   */
  async downloadTemplatesFile(): Promise<void> {
    const templates = await this.exportTemplates();
    
    const blob = new Blob([JSON.stringify(templates, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `node-templates-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  /**
   * Download a single template as JSON file
   */
  async downloadSingleTemplate(template: any): Promise<void> {
    // Export single template without id, createdAt, updatedAt for compatibility
    const exportData = {
      label: template.label,
      icon: template.icon,
      description: template.description,
      fields: template.fields,
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${template.label.toLowerCase()}-template.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  /**
   * Upload templates from JSON file
   * Supports both formats:
   * - Single template: {"label": "Person", "fields": [...]}
   * - Array of templates: [{"label": "Person"}, ...]
   */
  async uploadTemplatesFile(file: File, overwrite: boolean = false): Promise<TemplateImportResponse> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        try {
          const text = e.target?.result as string;
          const data = JSON.parse(text);
          
          // Support both single template object and array
          let templates: any;
          if (Array.isArray(data)) {
            templates = data;
          } else if (typeof data === 'object' && data !== null) {
            // Single template object
            templates = data;
          } else {
            throw new Error('Invalid file format: expected template object or array of templates');
          }
          
          const result = await this.importTemplates({ templates, overwrite });
          resolve(result);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }
}

// Export singleton instance
export const templateApi = new TemplateApiClient();

