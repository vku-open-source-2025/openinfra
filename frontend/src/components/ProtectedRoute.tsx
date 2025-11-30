import { Navigate, useNavigate } from '@tanstack/react-router';
import { useAuthStore } from '../stores/authStore';
import { useEffect, useState } from 'react';
import { authApi } from '../api/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'technician' | 'citizen';
  requiredPermission?: string;
}

export function ProtectedRoute({
  children,
  requiredRole,
  requiredPermission
}: ProtectedRouteProps) {
  const { isAuthenticated, user, refreshToken, setTokens } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated) {
        setIsChecking(false);
        return;
      }

      // Check role if required
      if (requiredRole && user?.role !== requiredRole) {
        navigate({ to: '/' });
        setIsChecking(false);
        return;
      }

      // Check permission if required
      if (requiredPermission && !user?.permissions.includes(requiredPermission)) {
        navigate({ to: '/' });
        setIsChecking(false);
        return;
      }

      // Try to refresh token if expired (simplified - in production, check token expiry)
      if (refreshToken) {
        try {
          const response = await authApi.refreshToken(refreshToken);
          setTokens(response.access_token, response.refresh_token);
        } catch (error) {
          // Token refresh failed, will be handled by httpClient interceptor
        }
      }

      setIsChecking(false);
    };

    checkAuth();
  }, [isAuthenticated, user, requiredRole, requiredPermission, refreshToken, setTokens, navigate]);

  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
}
