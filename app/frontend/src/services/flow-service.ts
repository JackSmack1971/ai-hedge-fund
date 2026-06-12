/* eslint-disable @typescript-eslint/no-explicit-any */
import { Flow } from '@/types/flow';
import { backendFetch, backendJsonHeaders } from '@/services/http';

export interface CreateFlowRequest {
  name: string;
  description?: string;
  nodes: any;
  edges: any;
  viewport?: any;
  data?: any;
  is_template?: boolean;
  tags?: string[];
}

export interface UpdateFlowRequest {
  name?: string;
  description?: string;
  nodes?: any;
  edges?: any;
  viewport?: any;
  data?: any;
  is_template?: boolean;
  tags?: string[];
}

export const flowService = {
  // Get all flows
  async getFlows(): Promise<Flow[]> {
    const response = await backendFetch('/flows/');
    if (!response.ok) {
      throw new Error('Failed to fetch flows');
    }
    return response.json();
  },

  // Get a specific flow
  async getFlow(id: number): Promise<Flow> {
    const response = await backendFetch(`/flows/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch flow');
    }
    return response.json();
  },

  // Create a new flow
  async createFlow(data: CreateFlowRequest): Promise<Flow> {
    const response = await backendFetch('/flows/', {
      method: 'POST',
      headers: backendJsonHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to create flow');
    }
    return response.json();
  },

  // Update an existing flow
  async updateFlow(id: number, data: UpdateFlowRequest): Promise<Flow> {
    const response = await backendFetch(`/flows/${id}`, {
      method: 'PUT',
      headers: backendJsonHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to update flow');
    }
    return response.json();
  },

  // Delete a flow
  async deleteFlow(id: number): Promise<void> {
    const response = await backendFetch(`/flows/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete flow');
    }
  },

  // Duplicate a flow
  async duplicateFlow(id: number, newName?: string): Promise<Flow> {
    const response = await backendFetch(`/flows/${id}/duplicate${newName ? `?new_name=${encodeURIComponent(newName)}` : ''}`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error('Failed to duplicate flow');
    }
    return response.json();
  },

  // Create a default flow for new users
  async createDefaultFlow(nodes: any, edges: any, viewport?: any): Promise<Flow> {
    return this.createFlow({
      name: 'My First Flow',
      description: 'Welcome to AI Hedge Fund! Start building your flow here.',
      nodes,
      edges,
      viewport,
    });
  },
};
