// API client for backend communication

import type { StructureRequest, StructureResponse, ApiError } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export class ApiClient {
  private controller: AbortController | null = null;

  async structureText(request: StructureRequest): Promise<StructureResponse> {
    this.controller = new AbortController();

    try {
      const response = await fetch(`${API_BASE_URL}/structure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: this.controller.signal,
      });

      if (!response.ok) {
        const error: ApiError = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const data: StructureResponse = await response.json();
      return data;
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

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  }

  cancel(): void {
    this.controller?.abort();
  }
}

export const apiClient = new ApiClient();

