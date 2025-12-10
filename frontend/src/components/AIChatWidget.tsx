import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, User, Code, Database, AlertCircle, Copy, Check, Play, ChevronDown, ChevronUp, ExternalLink, MapPin, Plus } from 'lucide-react';
import { type Asset, getAssetId } from '../api';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  toolInfo?: {
    tool: string;
    input?: string;
    output?: string;
  };
  codeBlocks?: {
    language: string;
    code: string;
  }[];
  apiCard?: ApiCardData;
}

interface ApiCardData {
  endpoint: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  description: string;
  params: ApiParam[];
}

interface ApiParam {
  name: string;
  type: 'string' | 'number' | 'boolean';
  description: string;
  default?: string | number | boolean;
  required?: boolean;
}

interface StreamChunk {
  type: 'token' | 'tool_start' | 'tool_end' | 'final' | 'error' | 'done';
  content?: string;
  tool?: string;
  input?: string;
  output?: string;
}

// API definitions for interactive testing
const API_DEFINITIONS: Record<string, ApiCardData> = {
  '/api/opendata/assets': {
    endpoint: '/api/opendata/assets',
    method: 'GET',
    description: 'Get infrastructure assets list (JSON-LD format)',
    params: [
      { name: 'skip', type: 'number', description: 'Records to skip', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Max records', default: 100, required: false },
      { name: 'feature_type', type: 'string', description: 'Filter by type (e.g., Power Station)', default: '', required: false },
      { name: 'feature_code', type: 'string', description: 'Filter by code (e.g., tram_dien)', default: '', required: false },
    ]
  },
  '/api/opendata/feature-types': {
    endpoint: '/api/opendata/feature-types',
    method: 'GET',
    description: 'Get asset types and counts',
    params: []
  },
  '/api/v1/assets': {
    endpoint: '/api/v1/assets',
    method: 'GET',
    description: 'Get assets list (internal)',
    params: [
      { name: 'skip', type: 'number', description: 'Records to skip', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Max records', default: 50, required: false },
      { name: 'feature_type', type: 'string', description: 'Filter by type', default: '', required: false },
    ]
  },
  '/api/v1/iot/sensors': {
    endpoint: '/api/v1/iot/sensors',
    method: 'GET',
    description: 'Get IoT sensors list',
    params: [
      { name: 'skip', type: 'number', description: 'Records to skip', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Max records', default: 50, required: false },
      { name: 'sensor_type', type: 'string', description: 'Sensor type', default: '', required: false },
      { name: 'status', type: 'string', description: 'Status (online/offline)', default: '', required: false },
    ]
  },
  '/api/v1/incidents': {
    endpoint: '/api/v1/incidents',
    method: 'GET',
    description: 'Get infrastructure incidents list',
    params: [
      { name: 'skip', type: 'number', description: 'Records to skip', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Max records', default: 50, required: false },
      { name: 'status', type: 'string', description: 'Status (open/in_progress/resolved)', default: '', required: false },
      { name: 'severity', type: 'string', description: 'Severity (low/medium/high/critical)', default: '', required: false },
    ]
  },
};

const WEBSOCKET_URL = import.meta.env.VITE_BASE_API_URL?.replace('http', 'ws').replace('/api/v1', '') + '/api/v1/ai/ws';
const API_BASE_URL = import.meta.env.VITE_BASE_API_URL?.replace('/api/v1', '') || '';

// API Card Component
function ApiCard({ apiData, onClose, initialResult }: {
  apiData: ApiCardData;
  onClose: () => void;
  initialResult?: { url?: string; status?: number; data_preview?: any };
}) {
  const [params, setParams] = useState<Record<string, string | number>>(() => {
    const initial: Record<string, string | number> = {};
    apiData.params.forEach(p => {
      initial[p.name] = p.default ?? '';
    });
    return initial;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(initialResult?.data_preview || null);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(!!initialResult);
  const [copiedResult, setCopiedResult] = useState(false);

  const buildUrl = () => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== '' && value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    const queryString = queryParams.toString();
    return `${API_BASE_URL}${apiData.endpoint}${queryString ? '?' + queryString : ''}`;
  };

  const callApi = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const url = buildUrl();
      const response = await fetch(url, {
        method: apiData.method,
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      setShowResult(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const copyResult = () => {
    if (result) {
      navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      setCopiedResult(true);
      setTimeout(() => setCopiedResult(false), 2000);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-blue-200 overflow-hidden shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-blue-100 flex items-center justify-between bg-gradient-to-r from-blue-50 to-cyan-50">
        <div className="flex items-center gap-2">
          <Code size={16} className="text-blue-500" />
          <span className="font-mono text-sm text-slate-700 font-semibold">API Tester</span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition">
          <X size={16} />
        </button>
      </div>

      {/* Endpoint Info */}
      <div className="px-4 py-3 border-b border-blue-100">
        <div className="flex items-center gap-2 mb-1">
          <span className={`px-2 py-0.5 rounded text-xs font-bold text-white ${apiData.method === 'GET' ? 'bg-green-500' :
            apiData.method === 'POST' ? 'bg-blue-500' :
              apiData.method === 'PUT' ? 'bg-amber-500' : 'bg-red-500'
            }`}>
            {apiData.method}
          </span>
          <code className="text-sm text-blue-600 font-mono">{apiData.endpoint}</code>
        </div>
        <p className="text-xs text-slate-500">{apiData.description}</p>
      </div>

      {/* Parameters */}
      {apiData.params.length > 0 && (
        <div className="px-4 py-3 border-b border-blue-100 space-y-3">
          <div className="text-xs text-slate-500 uppercase font-semibold tracking-wide">Parameters</div>
          {apiData.params.map(param => (
            <div key={param.name} className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <label className="text-sm text-slate-600 font-mono">
                  {param.name}
                  {param.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                <span className="text-xs text-slate-400">({param.type})</span>
              </div>
              <input
                type={param.type === 'number' ? 'number' : 'text'}
                value={params[param.name] ?? ''}
                onChange={(e) => setParams(prev => ({
                  ...prev,
                  [param.name]: param.type === 'number' ? (e.target.value ? Number(e.target.value) : '') : e.target.value
                }))}
                placeholder={param.description}
                className="w-full px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
              />
            </div>
          ))}
        </div>
      )}

      {/* URL Preview */}
      <div className="px-4 py-2 border-b border-blue-100 bg-slate-50">
        <div className="flex items-center gap-2">
          <ExternalLink size={12} className="text-slate-400" />
          <code className="text-xs text-slate-500 break-all">{buildUrl()}</code>
        </div>
      </div>

      {/* Call Button */}
      <div className="px-4 py-3 border-b border-blue-100">
        <button
          onClick={callApi}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
        >
          {isLoading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Calling API...</span>
            </>
          ) : (
            <>
              <Play size={16} />
              <span>Call API</span>
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-3 bg-red-50 border-b border-red-200">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle size={14} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="border-t border-blue-100">
          <button
            onClick={() => setShowResult(!showResult)}
            className="w-full px-4 py-2 flex items-center justify-between text-sm text-slate-600 hover:bg-blue-50 transition"
          >
            <span className="flex items-center gap-2">
              <Database size={14} className="text-green-500" />
              <span>Result</span>
              {Array.isArray(result.features) && (
                <span className="text-xs bg-green-100 text-green-600 px-2 py-0.5 rounded-full">
                  {result.features.length} items
                </span>
              )}
            </span>
            {showResult ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {showResult && (
            <div className="relative">
              <button
                onClick={copyResult}
                className="absolute top-2 right-2 p-1.5 bg-slate-200 hover:bg-slate-300 rounded text-slate-500 hover:text-slate-700 transition z-10"
                title="Copy JSON"
              >
                {copiedResult ? <Check size={12} /> : <Copy size={12} />}
              </button>
              <pre className="px-4 py-3 text-xs text-slate-700 bg-slate-50 overflow-auto max-h-60 font-mono border-t border-blue-100">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface AIChatWidgetProps {
  selectedAsset?: Asset | null;
}

export default function AIChatWidget({ selectedAsset }: AIChatWidgetProps = {}) {
  const [isOpen, setIsOpen] = useState(false);
  const [assetInContext, setAssetInContext] = useState<Asset | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I\'m OpenInfra AI Assistant. I can help you with:\n\n• Query infrastructure data (assets, sensors, incidents)\n• Guide API usage with JSON-LD format\n• Provide code examples\n• **Test APIs directly** - type "test api" to try!\n• **Select an asset on the map** to ask questions about it!\n\nHow can I help you?',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [currentToolInfo, setCurrentToolInfo] = useState<string | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const clientIdRef = useRef<string>(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const streamingMessageRef = useRef<string>('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset asset in context when selected asset changes (user needs to re-add it)
  useEffect(() => {
    if (selectedAsset && assetInContext && getAssetId(selectedAsset) !== getAssetId(assetInContext)) {
      setAssetInContext(null);
    }
  }, [selectedAsset, assetInContext]);

  const addAssetToContext = () => {
    if (selectedAsset) {
      setAssetInContext(selectedAsset);
      // Add a system message to inform the user
      const assetInfo = `Asset added to context:\n• Type: ${selectedAsset.feature_type}\n• Code: ${selectedAsset.feature_code}\n• ID: ${getAssetId(selectedAsset).slice(-6)}`;
      setMessages(prev => [...prev, {
        id: `asset-${Date.now()}`,
        role: 'system',
        content: `✅ ${assetInfo}\n\nYou can now ask questions about this asset!`,
        timestamp: new Date(),
      }]);
    }
  };

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${WEBSOCKET_URL}/${clientIdRef.current}`;
    console.log('Connecting to WebSocket:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      // Try to reconnect after 3 seconds
      setTimeout(() => {
        if (isOpen) connectWebSocket();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onmessage = (event) => {
      try {
        const chunk: StreamChunk = JSON.parse(event.data);
        handleStreamChunk(chunk);
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    wsRef.current = ws;
  }, [isOpen]);

  const handleStreamChunk = (chunk: StreamChunk) => {
    switch (chunk.type) {
      case 'token':
        streamingMessageRef.current += chunk.content || '';
        updateStreamingMessage(streamingMessageRef.current);
        break;

      case 'tool_start':
        setCurrentToolInfo(`🔧 Đang thực thi: ${chunk.tool}`);
        break;

      case 'tool_end':
        setCurrentToolInfo(null);
        break;

      case 'final':
        // Final response, update the message
        if (chunk.content) {
          updateStreamingMessage(chunk.content);
        }
        break;

      case 'error':
        setMessages(prev => [...prev.slice(0, -1), {
          id: Date.now().toString(),
          role: 'system',
          content: `❌ Lỗi: ${chunk.content}`,
          timestamp: new Date(),
        }]);
        setIsLoading(false);
        break;

      case 'done':
        setIsLoading(false);
        setCurrentToolInfo(null);
        streamingMessageRef.current = '';
        break;
    }
  };

  const updateStreamingMessage = (content: string) => {
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1];
      if (lastMessage?.role === 'assistant' && lastMessage.id === 'streaming') {
        return [
          ...prev.slice(0, -1),
          { ...lastMessage, content, timestamp: new Date() }
        ];
      }
      return prev;
    });
  };

  useEffect(() => {
    if (isOpen) {
      connectWebSocket();
    }

    return () => {
      wsRef.current?.close();
    };
  }, [isOpen, connectWebSocket]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    streamingMessageRef.current = '';

    // Add placeholder for assistant message
    const assistantMessage: Message = {
      id: 'streaming',
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, assistantMessage]);

    // Build chat history (last 10 messages)
    const history = messages
      .filter(m => m.role !== 'system')
      .slice(-10)
      .map(m => ({ role: m.role, content: m.content }));

    // Include asset context if available
    const assetContext = assetInContext ? {
      asset_id: getAssetId(assetInContext),
      feature_type: assetInContext.feature_type,
      feature_code: assetInContext.feature_code,
      geometry: assetInContext.geometry,
    } : null;

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat',
        message: userMessage.content,
        history,
        asset_context: assetContext,
      }));
    } else {
      // Fallback to REST API
      try {
        // Include asset context if available
        const assetContext = assetInContext ? {
          asset_id: getAssetId(assetInContext),
          feature_type: assetInContext.feature_type,
          feature_code: assetInContext.feature_code,
          geometry: assetInContext.geometry,
        } : null;

        const response = await fetch(`${import.meta.env.VITE_BASE_API_URL}/ai/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage.content,
            history,
            asset_context: assetContext,
          }),
        });

        const data = await response.json();
        updateStreamingMessage(data.response);
        setIsLoading(false);
      } catch (error) {
        console.error('Chat error:', error);
        updateStreamingMessage('❌ Không thể kết nối. Vui lòng thử lại.');
        setIsLoading(false);
      }
    }
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };


  // Parse code blocks from message content
  const renderMessage = (content: string) => {
    // First, convert <tool_output> and <tool_code> tags to code blocks
    let processedContent = content
      .replace(
        /<tool_output>([\s\S]*?)<\/tool_output>/g,
        (_, output) => '```json\n' + output.trim() + '\n```'
      )
      .replace(
        /<tool_code>([\s\S]*?)<\/tool_code>/g,
        (_, code) => '```python\n' + code.trim() + '\n```'
      );

    const parts = processedContent.split(/(```[\s\S]*?```)/g);

    return parts.map((part, idx) => {
      if (part.startsWith('```')) {
        const match = part.match(/```(\w+)?\n?([\s\S]*?)```/);
        if (match) {
          const lang = match[1] || 'text';
          const code = match[2].trim();

          // Handle api_card special block - parse and show interactive card
          if (lang === 'api_card') {
            try {
              const apiCardData = JSON.parse(code);
              // Extract endpoint from the api_card data
              const endpoint = apiCardData.endpoint || '';

              // Find matching API definition or create from response
              let matchedApi = Object.values(API_DEFINITIONS).find(
                api => endpoint.includes(api.endpoint) || api.endpoint.includes(endpoint)
              );

              if (!matchedApi && endpoint) {
                // Create dynamic API card from response data
                const params: ApiParam[] = [];
                if (apiCardData.params) {
                  Object.entries(apiCardData.params).forEach(([name, info]: [string, any]) => {
                    params.push({
                      name,
                      type: info.type === 'int' ? 'number' : 'string',
                      description: info.description || '',
                      default: info.default,
                      required: info.required || false
                    });
                  });
                }

                matchedApi = {
                  endpoint: endpoint,
                  method: (apiCardData.method || 'GET') as 'GET' | 'POST' | 'PUT' | 'DELETE',
                  description: apiCardData.description || '',
                  params
                };
              }

              if (matchedApi) {
                return (
                  <div key={idx} className="my-3">
                    <ApiCard
                      apiData={matchedApi}
                      onClose={() => { }}
                      initialResult={apiCardData.last_result}
                    />
                  </div>
                );
              }
            } catch (e) {
              console.error('Failed to parse api_card:', e);
            }
          }

          return (
            <div key={idx} className="my-2 rounded-lg overflow-hidden bg-slate-800 border border-slate-700">
              <div className="flex items-center justify-between px-3 py-1 bg-slate-900 text-xs text-slate-400">
                <span>{lang}</span>
                <button
                  onClick={() => copyCode(code)}
                  className="flex items-center gap-1 hover:text-white transition"
                >
                  {copiedCode === code ? (
                    <><Check size={12} /> Copied</>
                  ) : (
                    <><Copy size={12} /> Copy</>
                  )}
                </button>
              </div>
              <pre className="p-3 text-sm overflow-x-auto">
                <code className="text-green-400">{code}</code>
              </pre>
            </div>
          );
        }
      }

      // Handle bold text with **
      const processedText = part.split(/(\*\*[^*]+\*\*)/g).map((segment, segIdx) => {
        if (segment.startsWith('**') && segment.endsWith('**')) {
          return <strong key={segIdx} className="text-blue-600 font-semibold">{segment.slice(2, -2)}</strong>;
        }
        // Handle inline code with backticks
        return segment.split(/(`[^`]+`)/g).map((inlineSegment, inlineIdx) => {
          if (inlineSegment.startsWith('`') && inlineSegment.endsWith('`')) {
            return <code key={inlineIdx} className="bg-slate-100 px-1 rounded text-blue-600 border border-slate-200">{inlineSegment.slice(1, -1)}</code>;
          }
          return inlineSegment;
        });
      });

      // Regular text - preserve newlines
      return (
        <span key={idx} className="whitespace-pre-wrap">
          {processedText}
        </span>
      );
    });
  };

  return (
    <>
      {/* Chat button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 p-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all z-50 ${isOpen ? 'hidden' : ''}`}
      >
        <MessageCircle size={24} />
      </button>

      {/* Chat window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[440px] h-[650px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border border-blue-200 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white">
            <div className="flex items-center gap-2">
              <Bot size={20} />
              <div>
                <span className="font-semibold">OpenInfra AI</span>
                <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${isConnected ? 'bg-green-500/30' : 'bg-red-500/30'}`}>
                  {isConnected ? 'Connected' : 'Offline'}
                </span>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="hover:bg-white/20 p-1 rounded">
              <X size={20} />
            </button>
          </div>

          {/* Asset Context Banner */}
          {selectedAsset && !assetInContext && (
            <div className="px-4 py-3 border-b border-blue-100 bg-gradient-to-r from-green-50 to-emerald-50">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <MapPin size={16} className="text-green-600 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-green-800 truncate">
                      {selectedAsset.feature_type}
                    </p>
                    <p className="text-xs text-green-600 truncate">
                      {selectedAsset.feature_code} • ID: {getAssetId(selectedAsset).slice(-6)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={addAssetToContext}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg transition shadow-sm shrink-0"
                >
                  <Plus size={14} />
                  Add to Chat
                </button>
              </div>
            </div>
          )}

          {/* Asset in Context Indicator */}
          {assetInContext && (
            <div className="px-4 py-2 border-b border-blue-100 bg-gradient-to-r from-blue-50 to-cyan-50">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <p className="text-xs text-blue-700">
                  <span className="font-semibold">Context:</span> {assetInContext.feature_type} ({assetInContext.feature_code})
                </p>
                <button
                  onClick={() => setAssetInContext(null)}
                  className="ml-auto text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Clear
                </button>
              </div>
            </div>
          )}

          {/* Quick API Buttons */}
          <div className="px-3 py-2 border-b border-blue-100 bg-blue-50/50 flex gap-2 overflow-x-auto">
            {[
              { label: '📦 Assets', query: 'opendata assets' },
              { label: '📋 Types', query: 'feature types' },
              { label: '📡 Sensors', query: 'sensors' },
              { label: '🚨 Incidents', query: 'incidents' },
            ].map(btn => (
              <button
                key={btn.query}
                onClick={() => {
                  setInput(`test api ${btn.query}`);
                  setTimeout(() => sendMessage(), 50);
                }}
                disabled={isLoading}
                className="flex-shrink-0 text-xs px-3 py-1.5 bg-white hover:bg-blue-50 text-blue-700 rounded-full transition border border-blue-200 hover:border-blue-400 disabled:opacity-50 shadow-sm"
              >
                {btn.label}
              </button>
            ))}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-blue-50/30 to-white">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user'
                  ? 'bg-blue-500'
                  : msg.role === 'system'
                    ? 'bg-amber-500'
                    : 'bg-gradient-to-r from-blue-500 to-cyan-500'
                  }`}>
                  {msg.role === 'user' ? <User size={16} /> : msg.role === 'system' ? <AlertCircle size={16} /> : <Bot size={16} />}
                </div>
                <div className={`max-w-[85%] rounded-2xl px-4 py-2 ${msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : msg.role === 'system'
                    ? 'bg-amber-50 text-amber-800 border border-amber-200'
                    : 'bg-white text-slate-700 border border-blue-100 shadow-sm'
                  }`}>
                  {msg.role === 'assistant' && msg.content === '' && isLoading ? (
                    <div className="flex items-center gap-2">
                      <Loader2 size={16} className="animate-spin" />
                      <span className="text-slate-500">Thinking...</span>
                    </div>
                  ) : (
                    renderMessage(msg.content)
                  )}
                </div>
              </div>
            ))}

            {/* Tool execution indicator */}
            {currentToolInfo && (
              <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 rounded-lg px-3 py-2 border border-blue-200">
                <Database size={14} className="animate-pulse" />
                {currentToolInfo}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 border-t border-blue-100 bg-white">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder='Ask about API or type "test api"...'
                className="flex-1 bg-blue-50 text-slate-700 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 border border-blue-200 placeholder-slate-400"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white p-2 rounded-xl hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-md"
              >
                {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-2 text-center">
              OpenInfra AI • Query database & Test APIs
            </p>
          </div>
        </div>
      )}
    </>
  );
}
