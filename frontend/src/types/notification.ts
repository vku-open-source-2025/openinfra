export type NotificationType = 'alert' | 'maintenance' | 'incident' | 'budget' | 'system';

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: NotificationType;
  read: boolean;
  read_at?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
}
