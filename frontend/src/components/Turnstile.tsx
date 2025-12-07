import { useEffect, useRef, useCallback } from 'react';

declare global {
  interface Window {
    turnstile: {
      render: (container: HTMLElement, options: TurnstileOptions) => string;
      reset: (widgetId: string) => void;
      remove: (widgetId: string) => void;
    };
    onTurnstileLoad?: () => void;
  }
}

interface TurnstileOptions {
  sitekey: string;
  callback: (token: string) => void;
  'expired-callback'?: () => void;
  'error-callback'?: () => void;
  theme?: 'light' | 'dark' | 'auto';
  size?: 'normal' | 'compact';
}

interface TurnstileProps {
  siteKey: string;
  onVerify: (token: string) => void;
  onExpire?: () => void;
  onError?: () => void;
  theme?: 'light' | 'dark' | 'auto';
  size?: 'normal' | 'compact';
  className?: string;
}

const TURNSTILE_SCRIPT_URL = 'https://challenges.cloudflare.com/turnstile/v0/api.js';

export const Turnstile: React.FC<TurnstileProps> = ({
  siteKey,
  onVerify,
  onExpire,
  onError,
  theme = 'auto',
  size = 'normal',
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);
  const isScriptLoadedRef = useRef(false);

  const renderWidget = useCallback(() => {
    if (!containerRef.current || !window.turnstile || widgetIdRef.current) {
      return;
    }

    try {
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        callback: onVerify,
        'expired-callback': onExpire,
        'error-callback': onError,
        theme,
        size,
      });
    } catch (error) {
      console.error('Failed to render Turnstile widget:', error);
    }
  }, [siteKey, onVerify, onExpire, onError, theme, size]);

  useEffect(() => {
    // Check if script already loaded
    const existingScript = document.querySelector(`script[src*="turnstile"]`);
    
    if (existingScript) {
      // Script already exists
      if (window.turnstile) {
        renderWidget();
      } else {
        // Script exists but not loaded yet
        window.onTurnstileLoad = renderWidget;
      }
      return;
    }

    // Load script
    const script = document.createElement('script');
    script.src = `${TURNSTILE_SCRIPT_URL}?onload=onTurnstileLoad`;
    script.async = true;
    script.defer = true;

    window.onTurnstileLoad = () => {
      isScriptLoadedRef.current = true;
      renderWidget();
    };

    document.head.appendChild(script);

    return () => {
      // Cleanup widget on unmount
      if (widgetIdRef.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetIdRef.current);
        } catch (e) {
          // Ignore cleanup errors
        }
        widgetIdRef.current = null;
      }
    };
  }, [renderWidget]);

  return <div ref={containerRef} className={className} />;
};

export default Turnstile;
