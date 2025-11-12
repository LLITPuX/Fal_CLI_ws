/**
 * FalkorDB API client
 */

import type {
  CreateNodeRequest,
  CreateRelationshipRequest,
  GraphStats,
  NodeResponse,
  QueryRequest,
  QueryResponse,
  RelationshipResponse,
} from '../types/falkordb';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const FALKORDB_PREFIX = '/api/falkordb';

class FalkorDBApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${FALKORDB_PREFIX}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || `HTTP error ${response.status}`;
      throw new Error(errorMessage);
    }

    return response.json();
  }

  /**
   * Create a new node in the graph
   */
  async createNode(request: CreateNodeRequest): Promise<NodeResponse> {
    return this.request<NodeResponse>('/nodes', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Create a relationship between two nodes
   */
  async createRelationship(
    request: CreateRelationshipRequest
  ): Promise<RelationshipResponse> {
    return this.request<RelationshipResponse>('/relationships', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Execute a Cypher query
   */
  async executeQuery(request: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>('/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get graph statistics
   */
  async getStats(graphName?: string): Promise<GraphStats> {
    const query = graphName ? `?graph_name=${encodeURIComponent(graphName)}` : '';
    return this.request<GraphStats>(`/stats${query}`, {
      method: 'GET',
    });
  }

  /**
   * Check FalkorDB health
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>('/health', {
      method: 'GET',
    });
  }
}

export const falkorDBApi = new FalkorDBApiClient();

