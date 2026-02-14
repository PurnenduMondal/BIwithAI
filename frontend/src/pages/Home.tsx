import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PaperAirplaneIcon, SparklesIcon, BellIcon, UserCircleIcon, Cog6ToothIcon, ArrowRightOnRectangleIcon, PlusIcon, CircleStackIcon, Bars3Icon, ChatBubbleLeftRightIcon, XMarkIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';
import { chatApi, ChatMessage as ApiChatMessage, ChatSession } from '../api/chat';
import { useDataSources } from '../hooks/useDataSource';
import { useAuth } from '../hooks/useAuth';
import { getCurrentSubdomain } from '../utils/tenant';
import { Loader } from '../components/common/Loader';
import { ChartWidget } from '../components/widgets/ChartWidget';
import { TableWidget } from '../components/widgets/TableWidget';
import { MetricCard } from '../components/widgets/MetricCard';
import toast from 'react-hot-toast';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  widget_previews?: ApiChatMessage['widget_previews'];
  dashboard_id?: string;
}

export const Home = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDataSourceId, setSelectedDataSourceId] = useState<string>('');
  const [chatSessionId, setChatSessionId] = useState<string>('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const { data: dataSources, isLoading: isLoadingDataSources } = useDataSources();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Fetch chat sessions
  useEffect(() => {
    const fetchSessions = async () => {
      setIsLoadingSessions(true);
      try {
        const response = await chatApi.listSessions(1, 50);
        setChatSessions(response.sessions || response);
      } catch (error) {
        console.error('Failed to fetch chat sessions:', error);
      } finally {
        setIsLoadingSessions(false);
      }
    };
    fetchSessions();
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-select first data source
  useEffect(() => {
    if (dataSources && dataSources.length > 0 && !selectedDataSourceId) {
      setSelectedDataSourceId(dataSources[0].id);
    }
  }, [dataSources, selectedDataSourceId]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || !selectedDataSourceId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = '36px';
    }

    try {
      // Create session if it doesn't exist
      let sessionId = chatSessionId;
      if (!sessionId) {
        const session = await chatApi.createSession({
          data_source_id: selectedDataSourceId,
          title: 'New Chat',
        });
        sessionId = session.id;
        setChatSessionId(sessionId);
        refreshSessions();
      }

      const response = await chatApi.sendMessage(sessionId, {
        content: input,
      });
      
      const assistantMessage: Message = {
        id: response.id,
        role: 'assistant',
        content: response.content,
        timestamp: new Date(response.created_at),
        widget_previews: response.widget_previews,
        dashboard_id: response.dashboard_id,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      
      // If dashboard was created, show success message
      if (response.dashboard_id) {
        toast.success('Dashboard created! Click "View Dashboard" to see it.', {
          duration: 5000,
        });
      }
      
      // Refresh sessions to update message count
      refreshSessions();
    } catch (error: any) {
      toast.error(error.message || 'Failed to process query');
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your query. Please try again.',
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    
    // Auto-grow textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = '36px';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = Math.min(scrollHeight, 120) + 'px';
    }
  };

  const suggestedQueries = [
    'Show me top 5 products by sales',
    'What is the total revenue this year?',
    'Which region has the highest growth?',
    'Analyze sales trends by month',
  ];

  const refreshSessions = async () => {
    try {
      const response = await chatApi.listSessions(1, 50);
      setChatSessions(response.sessions || response);
    } catch (error) {
      console.error('Failed to refresh sessions:', error);
    }
  };

  const handleSuggestionClick = (query: string) => {
    setInput(query);
  };

  const handleLoadSession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      const session = await chatApi.getSession(sessionId);
      setChatSessionId(session.id);
      setSelectedDataSourceId(session.data_source_id || '');
      
      // Convert messages to our format
      const loadedMessages: Message[] = session.messages.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at),
        widget_previews: msg.widget_previews,
        dashboard_id: msg.dashboard_id,
      }));
      
      setMessages(loadedMessages);
      toast.success('Chat session loaded');
    } catch (error) {
      console.error('Failed to load session:', error);
      toast.error('Failed to load chat session');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    // Just clear the current session - new session will be created on first message
    setChatSessionId('');
    setMessages([]);
  };

  if (isLoadingDataSources) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader />
      </div>
    );
  }

  if (!dataSources || dataSources.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4">
        <SparklesIcon className="w-16 h-16 text-gray-400 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">No Data Sources Available</h2>
        <p className="text-gray-600 mb-6">
          Connect a data source to start asking questions about your data.
        </p>
        <button
          onClick={() => navigate('/data-sources/create')}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Connect Data Source
        </button>
      </div>
    );
  }

  return (
    <div className="relative h-full bg-white">
      {/* Main Content */}
      <div className="flex flex-col w-full h-full">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-3">
          <SparklesIcon className="w-7 h-7 text-blue-600" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">AI to BI Assistant</h1>
            <p className="text-xs text-gray-600">Ask questions about your data in natural language</p>
          </div>
          {(() => {
            const currentSubdomain = getCurrentSubdomain();
            const currentOrg = user?.organizations?.find(org => org.subdomain === currentSubdomain);
            return currentOrg ? (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg border border-blue-200">
                <BuildingOfficeIcon className="w-4 h-4" />
                <span className="text-sm font-medium">{currentOrg.org_name}</span>
              </div>
            ) : null;
          })()}
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Data Source:</label>
            <select
              value={selectedDataSourceId}
              onChange={(e) => setSelectedDataSourceId(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              {dataSources.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name}
                </option>
              ))}
            </select>
            <button
              onClick={() => navigate('/data-sources/create')}
              className="p-1.5 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
              title="Add new data source"
            >
              <PlusIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Notifications */}
          <button className="p-1.5 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 relative">
            <BellIcon className="w-5 h-5" />
            <span className="absolute top-0.5 right-0.5 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User Menu */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100"
            >
              <UserCircleIcon className="w-7 h-7 text-gray-600" />
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900">
                  {user?.full_name || user?.email}
                </p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
            </button>

            {/* Dropdown Menu */}
            {isMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                <div className="py-1">
                  <button
                    onClick={() => {
                      setIsMenuOpen(false);
                      navigate('/data-sources');
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <CircleStackIcon className="w-5 h-5 mr-3" />
                    Manage Data Sources
                  </button>
                  <button
                    onClick={() => {
                      setIsMenuOpen(false);
                      navigate('/settings');
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <Cog6ToothIcon className="w-5 h-5 mr-3" />
                    Settings
                  </button>
                  <button
                    onClick={() => {
                      setIsMenuOpen(false);
                      logout();
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Toggle Sidebar Button */}
          <button
            onClick={() => setIsSidebarOpen(true)}
            className={`p-1.5 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors ${
              isSidebarOpen ? 'invisible' : ''
            }`}
            title="Show chat history"
          >
            <Bars3Icon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 bg-gray-50">
        {messages.length === 0 ? (
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-8">
              <SparklesIcon className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                What would you like to know?
              </h2>
              <p className="text-gray-600">
                Ask questions about your data and get instant insights powered by AI
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {suggestedQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(query)}
                  className="p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all text-left"
                >
                  <p className="text-sm text-gray-700">{query}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {/* Render widget previews if available */}
                  {message.widget_previews && message.widget_previews.length > 0 && (
                    <div className="mt-4 space-y-4">
                      {message.widget_previews.map((preview, idx) => (
                        <div key={idx} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                          <h4 className="font-semibold text-gray-900 mb-2">
                            {preview.widget.title}
                          </h4>
                          {preview.widget.description && (
                            <p className="text-sm text-gray-600 mb-3">
                              {preview.widget.description}
                            </p>
                          )}
                          {preview.widget.ai_reasoning && (
                            <div className="mb-3 p-2 bg-blue-50 rounded text-xs text-blue-900">
                              <strong>AI Reasoning:</strong> {preview.widget.ai_reasoning}
                            </div>
                          )}
                          
                          {/* Render widget based on type */}
                          {['bar', 'line', 'pie', 'area', 'scatter', 'heatmap'].includes(preview.widget.widget_type) && (
                            <div className="bg-white p-4 rounded border border-gray-300 h-80">
                              <ChartWidget
                                widget={{
                                  id: preview.widget.id,
                                  widget_type: preview.widget.widget_type as any,
                                  title: preview.widget.title,
                                  query_config: preview.widget.query_config,
                                  chart_config: preview.widget.chart_config,
                                  position: preview.widget.position as { x: number; y: number; w: number; h: number; },
                                  dashboard_id: message.dashboard_id || '',
                                } as any}
                                data={preview.data}
                              />
                            </div>
                          )}
                            
                          {preview.widget.widget_type === 'metric' && (
                            <div className="bg-white p-4 rounded border border-gray-300">
                              <MetricCard
                                widget={{
                                  id: preview.widget.id,
                                  widget_type: 'metric',
                                  title: preview.widget.title,
                                  query_config: preview.widget.query_config,
                                  chart_config: preview.widget.chart_config,
                                  position: preview.widget.position as { x: number; y: number; w: number; h: number; },
                                  dashboard_id: message.dashboard_id || '',
                                } as any}
                                data={preview.data}
                              />
                            </div>
                          )}
                            
                          {preview.widget.widget_type === 'table' && (
                            <div className="bg-white p-4 rounded border border-gray-300 h-80 overflow-auto">
                              <TableWidget
                                widget={{
                                  id: preview.widget.id,
                                  widget_type: 'table',
                                  title: preview.widget.title,
                                  query_config: preview.widget.query_config,
                                  chart_config: preview.widget.chart_config,
                                  position: preview.widget.position as { x: number; y: number; w: number; h: number; },
                                  dashboard_id: message.dashboard_id || '',
                                } as any}
                                data={preview.data}
                              />
                            </div>
                          )}
                        </div>
                      ))}
                      
                      {/* View Dashboard Button */}
                      {message.dashboard_id && (
                        <button
                          onClick={() => navigate(`/dashboards/${message.dashboard_id}`)}
                          className="w-full mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          View Full Dashboard
                        </button>
                      )}
                    </div>
                  )}
                  
                  <p className="text-xs mt-2 opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                  <Loader />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="px-6 py-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-1">
            <div className="flex items-center space-x-3">
              <div className="flex-1">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInputChange}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about your data..."
                  rows={1}
                  disabled={isLoading || !selectedDataSourceId}
                  className="w-full px-3 py-2 border-0 focus:outline-none resize-none bg-transparent overflow-y-hidden"
                  style={{ height: '36px', maxHeight: '120px' }}
                />
              </div>
              
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading || !selectedDataSourceId}
                className="px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center flex-shrink-0"
              >
                <PaperAirplaneIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
          
          <p className="text-xs text-gray-500 mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
      </div>

      {/* Collapsible Sidebar - Right Side - Overlay */}
      <div
        className={`fixed top-0 right-0 h-full bg-gray-900 text-white transition-all duration-300 ease-in-out z-50 shadow-2xl ${
          isSidebarOpen ? 'w-64' : 'w-0'
        } overflow-hidden flex flex-col`}
      >
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ChatBubbleLeftRightIcon className="w-5 h-5" />
            <h2 className="font-semibold">Chat History</h2>
          </div>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="p-1 hover:bg-gray-800 rounded"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <button
          onClick={handleNewChat}
          className="m-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center justify-center gap-2 transition-colors"
          disabled={!selectedDataSourceId}
        >
          <PlusIcon className="w-5 h-5" />
          New Chat
        </button>

        <div className="flex-1 overflow-y-auto">
          {isLoadingSessions ? (
            <div className="flex items-center justify-center p-4">
              <Loader />
            </div>
          ) : (
            <div className="space-y-1 px-2">
              {chatSessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleLoadSession(session.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors ${
                    session.id === chatSessionId ? 'bg-gray-800' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <ChatBubbleLeftRightIcon className="w-4 h-4 mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {session.title || 'Untitled Chat'}
                      </p>
                      <p className="text-xs text-gray-400 truncate">
                        {new Date(session.last_message_at || session.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500">
                        {session.message_count} messages
                      </p>
                    </div>
                  </div>
                </button>
              ))}
              {chatSessions.length === 0 && (
                <p className="text-sm text-gray-400 text-center py-4">
                  No previous chats
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
