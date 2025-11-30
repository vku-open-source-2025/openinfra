import { httpClient } from '../lib/httpClient';
import type { Notification } from '../types/notification';

export interface NotificationListParams {
  skip?: number;
  limit?: number;
  unread_only?: boolean;
}

export const notificationsApi = {
  list: async (params?: NotificationListParams): Promise<Notification[]> => {
    const response = await httpClient.get<Notification[]>('/notifications', { params });
    return response.data;
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await httpClient.get<{ unread_count: number }>('/notifications/unread-count');
    return response.data;
  },

  markAsRead: async (id: string): Promise<Notification> => {
    const response = await httpClient.post<Notification>(`/notifications/${id}/read`);
    return response.data;
  },

  markAllAsRead: async (): Promise<{ message: string }> => {
    const response = await httpClient.post<{ message: string }>('/notifications/mark-all-read');
    return response.data;
  },
};
