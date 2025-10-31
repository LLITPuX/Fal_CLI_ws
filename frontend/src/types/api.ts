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

export interface StructureRequest {
  text: string;
  out_dir?: string;
  cli_command?: string;
  model?: string;
}

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
  | { status: 'success'; data: StructureResponse }
  | { status: 'error'; error: string };

