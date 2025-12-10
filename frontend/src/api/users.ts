import { httpClient } from '../lib/httpClient';
import type { User, UserCreateRequest, UserUpdateRequest, ProfileUpdateRequest } from '../types/user';

export interface UserListParams {
  skip?: number;
  limit?: number;
  role?: string;
  status?: string;
}

export const usersApi = {
  list: async (params?: UserListParams): Promise<User[]> => {
    const response = await httpClient.get<User[]>('/users', { params });
    return response.data;
  },

  listTechnicians: async (status?: string): Promise<User[]> => {
    const response = await httpClient.get<User[]>('/users/technicians', { 
      params: status ? { status } : undefined 
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await httpClient.get<User>('/users/me');
    return response.data;
  },

  updateCurrentUser: async (data: ProfileUpdateRequest): Promise<User> => {
    const response = await httpClient.put<User>('/users/me', data);
    return response.data;
  },

  getById: async (id: string): Promise<User> => {
    const response = await httpClient.get<User>(`/users/${id}`);
    return response.data;
  },

  create: async (data: UserCreateRequest): Promise<User> => {
    const response = await httpClient.post<User>('/users', data);
    return response.data;
  },

  update: async (id: string, data: UserUpdateRequest): Promise<User> => {
    const response = await httpClient.put<User>(`/users/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await httpClient.delete(`/users/${id}`);
  },
};
