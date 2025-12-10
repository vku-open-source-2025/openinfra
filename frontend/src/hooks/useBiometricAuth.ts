/**
 * WebAuthn Biometric Authentication Hook
 * Supports fingerprint, face recognition on supported devices
 */

import { useState, useCallback, useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';

// Storage keys
const BIOMETRIC_ENABLED_KEY = 'biometric_enabled';
const BIOMETRIC_CREDENTIAL_KEY = 'biometric_credential_id';
const BIOMETRIC_USER_KEY = 'biometric_user_data';

interface BiometricState {
  isAvailable: boolean;
  isEnabled: boolean;
  isLoading: boolean;
  error: string | null;
}

interface StoredCredential {
  credentialId: string;
  username: string;
  accessToken: string;
  refreshToken: string;
  user: any;
}

export function useBiometricAuth() {
  const { login } = useAuthStore();
  const [state, setState] = useState<BiometricState>({
    isAvailable: false,
    isEnabled: false,
    isLoading: false,
    error: null,
  });

  // Check if WebAuthn is available
  useEffect(() => {
    const checkAvailability = async () => {
      try {
        const available = 
          window.PublicKeyCredential !== undefined &&
          typeof window.PublicKeyCredential === 'function';
        
        if (available) {
          // Check if platform authenticator (fingerprint/face) is available
          const platformAvailable = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
          const enabled = localStorage.getItem(BIOMETRIC_ENABLED_KEY) === 'true';
          
          setState(prev => ({
            ...prev,
            isAvailable: platformAvailable,
            isEnabled: enabled && platformAvailable,
          }));
        }
      } catch (error) {
        console.error('Error checking biometric availability:', error);
      }
    };

    checkAvailability();
  }, []);

  // Generate random challenge
  const generateChallenge = useCallback((): ArrayBuffer => {
    const challenge = new Uint8Array(32);
    crypto.getRandomValues(challenge);
    return challenge.buffer as ArrayBuffer;
  }, []);

  // Convert ArrayBuffer to Base64
  const bufferToBase64 = useCallback((buffer: ArrayBuffer): string => {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }, []);

  // Convert Base64 to ArrayBuffer
  const base64ToBuffer = useCallback((base64: string): ArrayBuffer => {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }, []);

  // Register biometric credential after successful login
  const registerBiometric = useCallback(async (
    username: string,
    accessToken: string,
    refreshToken: string,
    user: any
  ): Promise<boolean> => {
    if (!state.isAvailable) {
      setState(prev => ({ ...prev, error: 'Biometric not available on this device' }));
      return false;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const challenge = generateChallenge();
      const userId = new TextEncoder().encode(username);

      const publicKeyCredentialCreationOptions: PublicKeyCredentialCreationOptions = {
        challenge,
        rp: {
          name: 'OpenInfra',
          id: window.location.hostname,
        },
        user: {
          id: userId,
          name: username,
          displayName: user.full_name || username,
        },
        pubKeyCredParams: [
          { alg: -7, type: 'public-key' },   // ES256
          { alg: -257, type: 'public-key' }, // RS256
        ],
        authenticatorSelection: {
          authenticatorAttachment: 'platform', // Use device biometric
          userVerification: 'required',
          residentKey: 'preferred',
        },
        timeout: 60000,
        attestation: 'none',
      };

      const credential = await navigator.credentials.create({
        publicKey: publicKeyCredentialCreationOptions,
      }) as PublicKeyCredential;

      if (!credential) {
        throw new Error('Failed to create credential');
      }

      // Store credential info locally (for demo - in production, send to server)
      const storedCredential: StoredCredential = {
        credentialId: bufferToBase64(credential.rawId),
        username,
        accessToken,
        refreshToken,
        user,
      };

      localStorage.setItem(BIOMETRIC_CREDENTIAL_KEY, storedCredential.credentialId);
      localStorage.setItem(BIOMETRIC_USER_KEY, JSON.stringify(storedCredential));
      localStorage.setItem(BIOMETRIC_ENABLED_KEY, 'true');

      setState(prev => ({ ...prev, isLoading: false, isEnabled: true }));
      return true;
    } catch (error: any) {
      console.error('Biometric registration error:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to register biometric',
      }));
      return false;
    }
  }, [state.isAvailable, generateChallenge, bufferToBase64]);

  // Authenticate using biometric
  const authenticateWithBiometric = useCallback(async (): Promise<boolean> => {
    if (!state.isEnabled) {
      setState(prev => ({ ...prev, error: 'Biometric not enabled' }));
      return false;
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const storedData = localStorage.getItem(BIOMETRIC_USER_KEY);
      if (!storedData) {
        throw new Error('No stored credentials found');
      }

      const stored: StoredCredential = JSON.parse(storedData);
      const challenge = generateChallenge();

      const publicKeyCredentialRequestOptions: PublicKeyCredentialRequestOptions = {
        challenge,
        rpId: window.location.hostname,
        allowCredentials: [
          {
            id: base64ToBuffer(stored.credentialId),
            type: 'public-key',
            transports: ['internal'],
          },
        ],
        userVerification: 'required',
        timeout: 60000,
      };

      const assertion = await navigator.credentials.get({
        publicKey: publicKeyCredentialRequestOptions,
      }) as PublicKeyCredential;

      if (!assertion) {
        throw new Error('Authentication failed');
      }

      // Biometric verified - login with stored credentials
      login(stored.accessToken, stored.refreshToken, stored.user);
      
      setState(prev => ({ ...prev, isLoading: false }));
      return true;
    } catch (error: any) {
      console.error('Biometric authentication error:', error);
      
      // Handle user cancellation
      if (error.name === 'NotAllowedError') {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Authentication cancelled',
        }));
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: error.message || 'Biometric authentication failed',
        }));
      }
      return false;
    }
  }, [state.isEnabled, generateChallenge, base64ToBuffer, login]);

  // Disable biometric
  const disableBiometric = useCallback(() => {
    localStorage.removeItem(BIOMETRIC_ENABLED_KEY);
    localStorage.removeItem(BIOMETRIC_CREDENTIAL_KEY);
    localStorage.removeItem(BIOMETRIC_USER_KEY);
    setState(prev => ({ ...prev, isEnabled: false }));
  }, []);

  // Update stored tokens (after token refresh)
  const updateStoredTokens = useCallback((accessToken: string, refreshToken: string) => {
    const storedData = localStorage.getItem(BIOMETRIC_USER_KEY);
    if (storedData) {
      const stored: StoredCredential = JSON.parse(storedData);
      stored.accessToken = accessToken;
      stored.refreshToken = refreshToken;
      localStorage.setItem(BIOMETRIC_USER_KEY, JSON.stringify(stored));
    }
  }, []);

  return {
    ...state,
    registerBiometric,
    authenticateWithBiometric,
    disableBiometric,
    updateStoredTokens,
  };
}
