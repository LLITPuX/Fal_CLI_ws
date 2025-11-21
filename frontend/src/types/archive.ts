// TypeScript types for Document Archiver System

export type FieldType =
  | "text"
  | "longtext"
  | "number"
  | "boolean"
  | "enum"
  | "date"
  | "url"
  | "email"
  | "array"
  | "object";

export interface FieldValidation {
  min?: number | null;
  max?: number | null;
  pattern?: string | null;
}

export interface NodeSchemaField {
  id: string;
  name: string;
  type: FieldType;
  label: string;
  required: boolean;
  default_value?: any | null;
  enum_values?: string[] | null;
  validation?: FieldValidation | null;
}

export interface NodeSchema {
  id: string;
  label: string;
  description: string;
  fields: NodeSchemaField[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface SchemaVersion {
  id: string;
  schema_id: string;
  version: number;
  content: Record<string, any>;
  created_at: string;
}

export interface PromptTemplate {
  id: string;
  name: string;
  content: string;
  placeholders: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface PromptVersion {
  id: string;
  prompt_id: string;
  version: number;
  content: string;
  created_at: string;
}

export interface DocumentType {
  id: string;
  name: string;
  file_extension: string;
  description: string;
  node_schemas: Record<string, string>; // label -> schema_id
  prompt_id: string;
  created_at: string;
  updated_at: string;
}

export interface ArchiveRequest {
  content: string;
  file_path: string;
  document_type: string;
  schema_id?: string | null;
  prompt_id?: string | null;
}

export interface ArchiveStats {
  document_id: string;
  rules_created: number;
  entities_created: number;
  relationships_created: number;
}

export interface ArchiveResponse {
  success: boolean;
  stats: ArchiveStats;
  message: string;
}

export interface PreviewRequest {
  content: string;
  document_type: string;
  schema_id?: string | null;
  prompt_id?: string | null;
}

export interface PreviewNode {
  label: string;
  properties: Record<string, any>;
}

export interface PreviewRelationship {
  from_label: string;
  to_label: string;
  relationship_type: string;
  properties: Record<string, any>;
}

export interface PreviewResponse {
  success: boolean;
  nodes: PreviewNode[];
  relationships: PreviewRelationship[];
  json_preview: Record<string, any>;
  message: string;
}

export interface CreateDocumentTypeRequest {
  name: string;
  file_extension: string;
  description: string;
  node_schemas: Record<string, NodeSchema>;
  prompt_template: PromptTemplate;
}

export interface CreateSchemaVersionRequest {
  schema_id: string;
  schema: NodeSchema;
}

export interface RollbackSchemaRequest {
  schema_id: string;
  version: number;
}

export interface CreatePromptVersionRequest {
  prompt_id: string;
  prompt: PromptTemplate;
}

export interface RollbackPromptRequest {
  prompt_id: string;
  version: number;
}

export interface DocumentTypeListResponse {
  success: boolean;
  document_types: DocumentType[];
  count: number;
  message: string;
}

export interface DocumentTypeResponse {
  success: boolean;
  document_type: DocumentType | null;
  message: string;
}

export interface SchemaResponse {
  success: boolean;
  schema: NodeSchema | null;
  message: string;
}

export interface SchemaVersionsResponse {
  success: boolean;
  versions: SchemaVersion[];
  current_version: number;
  message: string;
}

export interface PromptResponse {
  success: boolean;
  prompt: PromptTemplate | null;
  message: string;
}

export interface PromptVersionsResponse {
  success: boolean;
  versions: PromptVersion[];
  current_version: number;
  message: string;
}



