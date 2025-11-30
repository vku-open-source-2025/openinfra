export type UserRole = 'admin' | 'technician' | 'citizen' | 'manager';
export type UserStatus = 'active' | 'inactive' | 'suspended';

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  status: UserStatus;
  permissions: string[];
  department?: string;
  avatar_url?: string;
  language?: string;
  notification_preferences?: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface UserCreateRequest {
  username: string;
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  role: UserRole;
}

export interface UserUpdateRequest {
  email?: string;
  full_name?: string;
  phone?: string;
  role?: UserRole;
  status?: UserStatus;
  department?: string;
}

export interface ProfileUpdateRequest {
  email?: string;
  full_name?: string;
  phone?: string;
}
