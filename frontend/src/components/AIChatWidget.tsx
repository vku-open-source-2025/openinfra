import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, User, Code, Database, AlertCircle, Copy, Check, Play, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

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
    description: 'Lấy danh sách tài sản hạ tầng (JSON-LD format)',
    params: [
      { name: 'skip', type: 'number', description: 'Số bản ghi bỏ qua', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Số bản ghi tối đa', default: 100, required: false },
      { name: 'feature_type', type: 'string', description: 'Lọc theo loại (vd: Trạm điện)', default: '', required: false },
      { name: 'feature_code', type: 'string', description: 'Lọc theo mã (vd: tram_dien)', default: '', required: false },
    ]
  },
  '/api/opendata/feature-types': {
    endpoint: '/api/opendata/feature-types',
    method: 'GET',
    description: 'Lấy danh sách các loại tài sản và số lượng',
    params: []
  },
  '/api/v1/assets': {
    endpoint: '/api/v1/assets',
    method: 'GET',
    description: 'Lấy danh sách assets (nội bộ)',
    params: [
      { name: 'skip', type: 'number', description: 'Số bản ghi bỏ qua', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Số bản ghi tối đa', default: 50, required: false },
      { name: 'feature_type', type: 'string', description: 'Lọc theo loại', default: '', required: false },
    ]
  },
  '/api/v1/iot/sensors': {
    endpoint: '/api/v1/iot/sensors',
    method: 'GET',
    description: 'Lấy danh sách cảm biến IoT',
    params: [
      { name: 'skip', type: 'number', description: 'Số bản ghi bỏ qua', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Số bản ghi tối đa', default: 50, required: false },
      { name: 'sensor_type', type: 'string', description: 'Loại cảm biến', default: '', required: false },
      { name: 'status', type: 'string', description: 'Trạng thái (online/offline)', default: '', required: false },
    ]
  },
  '/api/v1/incidents': {
    endpoint: '/api/v1/incidents',
    method: 'GET',
    description: 'Lấy danh sách sự cố hạ tầng',
    params: [
      { name: 'skip', type: 'number', description: 'Số bản ghi bỏ qua', default: 0, required: false },
      { name: 'limit', type: 'number', description: 'Số bản ghi tối đa', default: 50, required: false },
      { name: 'status', type: 'string', description: 'Trạng thái (open/in_progress/resolved)', default: '', required: false },
      { name: 'severity', type: 'string', description: 'Mức độ (low/medium/high/critical)', default: '', required: false },
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
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-600 overflow-hidden shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between bg-gradient-to-r from-blue-600/20 to-purple-600/20">
        <div className="flex items-center gap-2">
          <Code size={16} className="text-blue-400" />
          <span className="font-mono text-sm text-white font-semibold">API Tester</span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-white transition">
          <X size={16} />
        </button>
      </div>

      {/* Endpoint Info */}
      <div className="px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2 mb-1">
          <span className={`px-2 py-0.5 rounded text-xs font-bold ${apiData.method === 'GET' ? 'bg-green-600' :
            apiData.method === 'POST' ? 'bg-blue-600' :
              apiData.method === 'PUT' ? 'bg-yellow-600' : 'bg-red-600'
            }`}>
            {apiData.method}
          </span>
          <code className="text-sm text-blue-300 font-mono">{apiData.endpoint}</code>
        </div>
        <p className="text-xs text-gray-400">{apiData.description}</p>
      </div>

      {/* Parameters */}
      {apiData.params.length > 0 && (
        <div className="px-4 py-3 border-b border-gray-700 space-y-3">
          <div className="text-xs text-gray-400 uppercase font-semibold tracking-wide">Parameters</div>
          {apiData.params.map(param => (
            <div key={param.name} className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-300 font-mono">
                  {param.name}
                  {param.required && <span className="text-red-400 ml-1">*</span>}
                </label>
                <span className="text-xs text-gray-500">({param.type})</span>
              </div>
              <input
                type={param.type === 'number' ? 'number' : 'text'}
                value={params[param.name] ?? ''}
                onChange={(e) => setParams(prev => ({
                  ...prev,
                  [param.name]: param.type === 'number' ? (e.target.value ? Number(e.target.value) : '') : e.target.value
                }))}
                placeholder={param.description}
                className="w-full px-3 py-1.5 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              />
            </div>
          ))}
        </div>
      )}

      {/* URL Preview */}
      <div className="px-4 py-2 border-b border-gray-700 bg-gray-900/50">
        <div className="flex items-center gap-2">
          <ExternalLink size={12} className="text-gray-500" />
          <code className="text-xs text-gray-400 break-all">{buildUrl()}</code>
        </div>
      </div>

      {/* Call Button */}
      <div className="px-4 py-3 border-b border-gray-700">
        <button
          onClick={callApi}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
        >
          {isLoading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span>Đang gọi API...</span>
            </>
          ) : (
            <>
              <Play size={16} />
              <span>Gọi API</span>
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-3 bg-red-900/30 border-b border-red-700">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle size={14} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="border-t border-gray-700">
          <button
            onClick={() => setShowResult(!showResult)}
            className="w-full px-4 py-2 flex items-center justify-between text-sm text-gray-300 hover:bg-gray-800 transition"
          >
            <span className="flex items-center gap-2">
              <Database size={14} className="text-green-400" />
              <span>Kết quả</span>
              {Array.isArray(result.features) && (
                <span className="text-xs bg-green-600/30 text-green-400 px-2 py-0.5 rounded-full">
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
                className="absolute top-2 right-2 p-1.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-400 hover:text-white transition z-10"
                title="Copy JSON"
              >
                {copiedResult ? <Check size={12} /> : <Copy size={12} />}
              </button>
              <pre className="px-4 py-3 text-xs text-green-300 bg-gray-900 overflow-auto max-h-60 font-mono">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AIChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Xin chào! Tôi là trợ lý AI của OpenInfra. Tôi có thể giúp bạn:\n\n• Truy vấn dữ liệu hạ tầng (assets, sensors, incidents)\n• Hướng dẫn sử dụng API với JSON-LD\n• Cung cấp code examples\n• **Test API trực tiếp** - gõ "test api" để thử!\n\nBạn muốn hỏi gì?',
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

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat',
        message: userMessage.content,
        history,
      }));
    } else {
      // Fallback to REST API
      try {
        const response = await fetch(`${import.meta.env.VITE_BASE_API_URL}/ai/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage.content,
            history,
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
    const parts = content.split(/(```[\s\S]*?```)/g);

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
            <div key={idx} className="my-2 rounded-lg overflow-hidden bg-gray-900">
              <div className="flex items-center justify-between px-3 py-1 bg-gray-800 text-xs text-gray-400">
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
          return <strong key={segIdx} className="text-blue-300">{segment.slice(2, -2)}</strong>;
        }
        // Handle inline code with backticks
        return segment.split(/(`[^`]+`)/g).map((inlineSegment, inlineIdx) => {
          if (inlineSegment.startsWith('`') && inlineSegment.endsWith('`')) {
            return <code key={inlineIdx} className="bg-gray-800 px-1 rounded text-blue-300">{inlineSegment.slice(1, -1)}</code>;
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
        className={`fixed bottom-6 right-6 p-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all z-50 ${isOpen ? 'hidden' : ''}`}
      >
        <MessageCircle size={24} />
      </button>

      {/* Chat window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[440px] h-[650px] bg-gray-900 rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-700 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
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

          {/* Quick API Buttons */}
          <div className="px-3 py-2 border-b border-gray-700 flex gap-2 overflow-x-auto">
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
                className="flex-shrink-0 text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full transition border border-gray-700 hover:border-blue-500 disabled:opacity-50"
              >
                {btn.label}
              </button>
            ))}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user'
                  ? 'bg-blue-600'
                  : msg.role === 'system'
                    ? 'bg-yellow-600'
                    : 'bg-purple-600'
                  }`}>
                  {msg.role === 'user' ? <User size={16} /> : msg.role === 'system' ? <AlertCircle size={16} /> : <Bot size={16} />}
                </div>
                <div className={`max-w-[85%] rounded-2xl px-4 py-2 ${msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : msg.role === 'system'
                    ? 'bg-yellow-900/50 text-yellow-200 border border-yellow-700'
                    : 'bg-gray-800 text-gray-100'
                  }`}>
                  {msg.role === 'assistant' && msg.content === '' && isLoading ? (
                    <div className="flex items-center gap-2">
                      <Loader2 size={16} className="animate-spin" />
                      <span className="text-gray-400">Đang suy nghĩ...</span>
                    </div>
                  ) : (
                    renderMessage(msg.content)
                  )}
                </div>
              </div>
            ))}

            {/* Tool execution indicator */}
            {currentToolInfo && (
              <div className="flex items-center gap-2 text-sm text-purple-400 bg-purple-900/20 rounded-lg px-3 py-2">
                <Database size={14} className="animate-pulse" />
                {currentToolInfo}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder='Hỏi về API hoặc gõ "test api"...'
                className="flex-1 bg-gray-800 text-white rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="bg-blue-600 text-white p-2 rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Powered by Gemini 2.5 Flash • Query database & Test APIs
            </p>
          </div>
        </div>
      )}
    </>
  );
}
