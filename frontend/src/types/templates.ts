/**
 * TypeScript types for node templates
 */

export type FieldType = 
  | 'text' 
  | 'longtext' 
  | 'number' 
  | 'boolean' 
  | 'enum' 
  | 'date' 
  | 'url' 
  | 'email';

export interface FieldValidation {
  min?: number;
  max?: number;
  pattern?: string;
}

export interface TemplateField {
  id: string;
  name: string;
  type: FieldType;
  label: string;
  required: boolean;
  placeholder?: string;
  defaultValue?: any;
  enumValues?: string[];
  validation?: FieldValidation;
}

export interface NodeTemplate {
  id: string;
  label: string;
  icon?: string;
  description: string;
  fields: TemplateField[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateTemplateRequest {
  label: string;
  icon?: string;
  description: string;
  fields: TemplateField[];
}

export interface UpdateTemplateRequest {
  icon?: string;
  description?: string;
  fields?: TemplateField[];
}

export interface TemplateResponse {
  success: boolean;
  template?: NodeTemplate;
  message: string;
}

export interface TemplateListResponse {
  success: boolean;
  templates: NodeTemplate[];
  count: number;
  message: string;
}

export interface TemplateMigrationRequest {
  templateId: string;
  applyDefaults: boolean;
}

export interface TemplateMigrationResponse {
  success: boolean;
  nodesUpdated: number;
  fieldsAdded: string[];
  message: string;
}

export interface TemplateExportResponse {
  success: boolean;
  templates: any[];
  count: number;
  message: string;
}

export interface TemplateImportRequest {
  templates: any[];
  overwrite: boolean;
}

export interface TemplateImportResponse {
  success: boolean;
  imported: number;
  skipped: number;
  errors: string[];
  message: string;
}

export interface CreateNodeFromTemplateRequest {
  templateId: string;
  label: string;
  fieldValues: Record<string, any>;
}

