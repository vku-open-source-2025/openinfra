import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, User, Code, Database, AlertCircle, Copy, Check } from 'lucide-react';

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
}

interface StreamChunk {
  type: 'token' | 'tool_start' | 'tool_end' | 'final' | 'error' | 'done';
  content?: string;
  tool?: string;
  input?: string;
  output?: string;
}

const WEBSOCKET_URL = import.meta.env.VITE_BASE_API_URL?.replace('http', 'ws').replace('/api/v1', '') + '/api/v1/ai/ws';

export default function AIChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Xin chào! Tôi là trợ lý AI của OpenInfra. Tôi có thể giúp bạn:\n\n• Truy vấn dữ liệu hạ tầng (assets, sensors, incidents)\n• Hướng dẫn sử dụng API với JSON-LD\n• Cung cấp code examples\n\nBạn muốn hỏi gì?',
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
      
      // Regular text - preserve newlines
      return (
        <span key={idx} className="whitespace-pre-wrap">
          {part}
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
        <div className="fixed bottom-6 right-6 w-[420px] h-[600px] bg-gray-900 rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-700 overflow-hidden">
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

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  msg.role === 'user' 
                    ? 'bg-blue-600' 
                    : msg.role === 'system' 
                      ? 'bg-yellow-600' 
                      : 'bg-purple-600'
                }`}>
                  {msg.role === 'user' ? <User size={16} /> : msg.role === 'system' ? <AlertCircle size={16} /> : <Bot size={16} />}
                </div>
                <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                  msg.role === 'user'
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
                placeholder="Hỏi về dữ liệu hoặc API..."
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
              Powered by Gemini AI • Query database & API docs
            </p>
          </div>
        </div>
      )}
    </>
  );
}
