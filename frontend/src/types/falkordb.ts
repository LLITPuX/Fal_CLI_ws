/**
 * FalkorDB TypeScript types
 */

export interface NodeProperties {
  [key: string]: string | number | boolean;
}

export interface CreateNodeRequest {
  label: string;
  properties: NodeProperties;
  template_id?: string;
}

export interface NodeResponse {
  success: boolean;
  node_id?: string;
  label: string;
  properties: NodeProperties;
  message: string;
}

export interface CreateRelationshipRequest {
  from_label: string;
  from_properties: NodeProperties;
  to_label: string;
  to_properties: NodeProperties;
  relationship_type: string;
  relationship_properties?: NodeProperties;
}

export interface RelationshipResponse {
  success: boolean;
  from_node: string;
  to_node: string;
  relationship_type: string;
  message: string;
}

export interface QueryRequest {
  query: string;
  params?: Record<string, unknown>;
}

export interface QueryResponse {
  success: boolean;
  results: QueryResult[];
  row_count: number;
  execution_time_ms: number;
  message: string;
}

export interface QueryResult {
  [key: string]: unknown;
}

export interface GraphStats {
  node_count: number;
  edge_count: number;
  labels: string[];
  relationship_types: string[];
  graph_name: string;
}

export type LoadingStatus = 'idle' | 'loading' | 'success' | 'error';

export interface FalkorDBState {
  status: LoadingStatus;
  data?: QueryResponse | NodeResponse | RelationshipResponse;
  error?: string;
}

