import { httpClient } from '../lib/httpClient';
import type {
  Budget,
  BudgetTransaction,
  BudgetCreateRequest,
  BudgetUpdateRequest,
  BudgetTransactionCreateRequest,
} from '../types/budget';

export interface BudgetListParams {
  skip?: number;
  limit?: number;
  fiscal_year?: number;
  status?: string;
  category?: string;
}

export const budgetsApi = {
  list: async (params?: BudgetListParams): Promise<Budget[]> => {
    const response = await httpClient.get<Budget[]>('/budgets', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Budget> => {
    const response = await httpClient.get<Budget>(`/budgets/${id}`);
    return response.data;
  },

  create: async (data: BudgetCreateRequest): Promise<Budget> => {
    const response = await httpClient.post<Budget>('/budgets', data);
    return response.data;
  },

  update: async (id: string, data: BudgetUpdateRequest): Promise<Budget> => {
    const response = await httpClient.put<Budget>(`/budgets/${id}`, data);
    return response.data;
  },

  submit: async (id: string): Promise<Budget> => {
    const response = await httpClient.post<Budget>(`/budgets/${id}/submit`);
    return response.data;
  },

  approve: async (id: string): Promise<Budget> => {
    const response = await httpClient.post<Budget>(`/budgets/${id}/approve`);
    return response.data;
  },

  getTransactions: async (id: string, params?: { skip?: number; limit?: number }): Promise<BudgetTransaction[]> => {
    const response = await httpClient.get<BudgetTransaction[]>(`/budgets/${id}/transactions`, { params });
    return response.data;
  },

  createTransaction: async (id: string, data: BudgetTransactionCreateRequest): Promise<BudgetTransaction> => {
    const response = await httpClient.post<BudgetTransaction>(`/budgets/${id}/transactions`, data);
    return response.data;
  },

  approveTransaction: async (transactionId: string): Promise<BudgetTransaction> => {
    const response = await httpClient.post<BudgetTransaction>(`/budgets/transactions/${transactionId}/approve`);
    return response.data;
  },
};
