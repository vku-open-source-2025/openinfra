import { useState, useEffect } from 'react';
import { useNavigate, Link } from '@tanstack/react-router';
import { useAuthStore } from '../stores/authStore';
import { authApi } from '../api/auth';
import { useBiometricAuth } from '../hooks/useBiometricAuth';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Fingerprint, Loader2 } from 'lucide-react';

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const {
    isAvailable: biometricAvailable,
    isEnabled: biometricEnabled,
    isLoading: biometricLoading,
    error: biometricError,
    registerBiometric,
    authenticateWithBiometric,
  } = useBiometricAuth();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showBiometricSetup, setShowBiometricSetup] = useState(false);
  const [pendingCredentials, setPendingCredentials] = useState<{
    accessToken: string;
    refreshToken: string;
    user: any;
  } | null>(null);

  // Auto-trigger biometric if enabled
  useEffect(() => {
    if (biometricEnabled && !biometricLoading) {
      handleBiometricLogin();
    }
  }, [biometricEnabled]);

  const handleBiometricLogin = async () => {
    const success = await authenticateWithBiometric();
    if (success) {
      navigate({ to: '/admin' });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authApi.login(formData);
      
      // If biometric is available but not enabled, offer to set up
      if (biometricAvailable && !biometricEnabled) {
        setPendingCredentials({
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
          user: response.user,
        });
        setShowBiometricSetup(true);
        setLoading(false);
        return;
      }

      login(response.access_token, response.refresh_token, response.user);
      navigate({ to: '/admin' });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSetupBiometric = async () => {
    if (!pendingCredentials) return;
    
    const success = await registerBiometric(
      formData.username,
      pendingCredentials.accessToken,
      pendingCredentials.refreshToken,
      pendingCredentials.user
    );

    // Login regardless of biometric setup result
    login(
      pendingCredentials.accessToken,
      pendingCredentials.refreshToken,
      pendingCredentials.user
    );
    navigate({ to: '/admin' });
  };

  const handleSkipBiometric = () => {
    if (!pendingCredentials) return;
    
    login(
      pendingCredentials.accessToken,
      pendingCredentials.refreshToken,
      pendingCredentials.user
    );
    navigate({ to: '/admin' });
  };

  // Biometric setup dialog
  if (showBiometricSetup) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <Fingerprint className="w-8 h-8 text-blue-600" />
            </div>
            <CardTitle>Enable Biometric Login?</CardTitle>
            <CardDescription>
              Use fingerprint or face recognition for faster, secure login next time
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button 
              onClick={handleSetupBiometric} 
              className="w-full"
              disabled={biometricLoading}
            >
              {biometricLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Setting up...
                </>
              ) : (
                <>
                  <Fingerprint className="w-4 h-4 mr-2" />
                  Enable Biometric Login
                </>
              )}
            </Button>
            <Button 
              variant="outline" 
              onClick={handleSkipBiometric}
              className="w-full"
              disabled={biometricLoading}
            >
              Skip for now
            </Button>
            {biometricError && (
              <p className="text-sm text-red-600 text-center">{biometricError}</p>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to your account</CardTitle>
          <CardDescription>Enter your credentials to access the system</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Biometric Login Button */}
          {biometricEnabled && (
            <div className="mb-6">
              <Button
                type="button"
                variant="outline"
                className="w-full h-16 border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50"
                onClick={handleBiometricLogin}
                disabled={biometricLoading}
              >
                {biometricLoading ? (
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                ) : (
                  <div className="flex flex-col items-center">
                    <Fingerprint className="w-6 h-6 text-blue-600 mb-1" />
                    <span className="text-sm text-blue-600">Use Biometric</span>
                  </div>
                )}
              </Button>
              {biometricError && (
                <p className="text-xs text-red-600 text-center mt-2">{biometricError}</p>
              )}
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">or continue with password</span>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                placeholder="Enter your username"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Enter your password"
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>

            <div className="text-center text-sm">
              <span className="text-gray-600">Don't have an account? </span>
              <Link to="/register" className="text-blue-600 hover:text-blue-500">
                Register here
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
