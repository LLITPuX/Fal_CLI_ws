// TypeScript types for API communication

export interface StructuredDoc {
  title: string;
  date_iso: string;
  summary: string;
  tags: string[];
  sections: Section[];
}

export interface Section {
  name: string;
  content: string;
}

export interface ProcessingMetrics {
  model: string;
  processing_time_seconds: number;
  input_characters: number;
  output_characters: number;
  input_tokens_estimate: number;
  output_tokens_estimate: number;
}

export interface ModelResult {
  id: string;
  json_path: string;
  data: StructuredDoc | null;
  metrics: ProcessingMetrics | null;
  error: string | null;
}

export interface StructureRequest {
  text: string;
  out_dir?: string;
  cli_command?: string;
  model?: string;
}

export interface MultiModelResponse {
  results: ModelResult[];
  total_processing_time_seconds: number;
}

// Legacy response for backward compatibility
export interface StructureResponse {
  id: string;
  json_path: string;
  data: StructuredDoc;
}

export interface ApiError {
  detail: string;
}

export type LoadingState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: MultiModelResponse }
  | { status: 'error'; error: string };

