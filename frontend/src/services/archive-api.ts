// API client for document archiver system

import type {
  ArchiveRequest,
  ArchiveResponse,
  CreateDocumentTypeRequest,
  CreatePromptVersionRequest,
  CreateSchemaVersionRequest,
  DocumentType,
  DocumentTypeListResponse,
  DocumentTypeResponse,
  PreviewRequest,
  PreviewResponse,
  PromptResponse,
  PromptTemplate,
  PromptVersionsResponse,
  RollbackPromptRequest,
  RollbackSchemaRequest,
  SchemaResponse,
  SchemaVersionsResponse,
  NodeSchema,
} from '../types/archive';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export class ArchiveApiClient {
  private controller: AbortController | null = null;

  private async fetchJson<T>(
    url: string,
    options?: RequestInit
  ): Promise<T> {
    this.controller = new AbortController();

    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        signal: this.controller.signal,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request was cancelled');
        }
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  // Document archiving
  async archiveDocument(request: ArchiveRequest): Promise<ArchiveResponse> {
    return this.fetchJson<ArchiveResponse>('/archive/document', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async previewArchive(request: PreviewRequest): Promise<PreviewResponse> {
    return this.fetchJson<PreviewResponse>('/archive/preview', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Document types
  async getDocumentTypes(): Promise<DocumentTypeListResponse> {
    return this.fetchJson<DocumentTypeListResponse>('/archive/document-types');
  }

  async getDocumentType(typeId: string): Promise<DocumentType> {
    const response = await this.fetchJson<DocumentTypeResponse>(
      `/archive/document-types/${typeId}`
    );
    if (!response.document_type) {
      throw new Error('Document type not found');
    }
    return response.document_type;
  }

  async createDocumentType(
    request: CreateDocumentTypeRequest
  ): Promise<DocumentType> {
    const response = await this.fetchJson<DocumentTypeResponse>(
      '/archive/document-types',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    if (!response.document_type) {
      throw new Error('Failed to create document type');
    }
    return response.document_type;
  }

  // Schemas
  async getSchemasForType(
    typeId: string,
    label?: string
  ): Promise<NodeSchema> {
    const url = label
      ? `/archive/document-types/${typeId}/schemas?label=${encodeURIComponent(label)}`
      : `/archive/document-types/${typeId}/schemas`;
    
    const response = await this.fetchJson<SchemaResponse>(url);
    if (!response.schema) {
      throw new Error('Schema not found');
    }
    return response.schema;
  }

  async createSchemaVersion(
    request: CreateSchemaVersionRequest
  ): Promise<NodeSchema> {
    const response = await this.fetchJson<SchemaResponse>(
      `/archive/document-types/${request.schema_id}/schemas`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    if (!response.schema) {
      throw new Error('Failed to create schema version');
    }
    return response.schema;
  }

  async getSchemaVersions(schemaId: string): Promise<SchemaVersionsResponse> {
    return this.fetchJson<SchemaVersionsResponse>(
      `/archive/schemas/${schemaId}/versions`
    );
  }

  async rollbackSchema(request: RollbackSchemaRequest): Promise<NodeSchema> {
    const response = await this.fetchJson<SchemaResponse>(
      `/archive/schemas/${request.schema_id}/rollback`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    if (!response.schema) {
      throw new Error('Failed to rollback schema');
    }
    return response.schema;
  }

  // Prompts
  async getPrompt(promptId: string): Promise<PromptTemplate> {
    // Get prompt from document type (prompt_id is stored in document type)
    // For now, we'll need to get it from document type or create a direct endpoint
    // Temporary: Get from document type's prompt_id
    const response = await this.fetchJson<PromptResponse>(
      `/archive/prompts/${promptId}`
    );
    if (!response.prompt) {
      // Fallback: try to get from document type
      // This is a workaround until we have a direct endpoint
      throw new Error('Prompt not found');
    }
    return response.prompt;
  }

  async getPromptVersions(promptId: string): Promise<PromptVersionsResponse> {
    return this.fetchJson<PromptVersionsResponse>(
      `/archive/prompts/${promptId}/versions`
    );
  }

  async rollbackPrompt(request: RollbackPromptRequest): Promise<PromptTemplate> {
    const response = await this.fetchJson<PromptResponse>(
      `/archive/prompts/${request.prompt_id}/rollback`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    if (!response.prompt) {
      throw new Error('Failed to rollback prompt');
    }
    return response.prompt;
  }

  async createPromptVersion(
    request: CreatePromptVersionRequest
  ): Promise<PromptTemplate> {
    const response = await this.fetchJson<PromptResponse>(
      `/archive/prompts/${request.prompt_id}/versions`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
    if (!response.prompt) {
      throw new Error('Failed to create prompt version');
    }
    return response.prompt;
  }

  cancel(): void {
    if (this.controller) {
      this.controller.abort();
    }
  }
}

export const archiveApi = new ArchiveApiClient();

