/**
 * API service for communicating with the backend.
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

/**
 * Public API
 */
export const publicAPI = {
  // Get supported language pairs
  getLanguages: () => api.get('/api/languages'),
  
  // Health check
  healthCheck: () => api.get('/api/health'),
  
  // Login
  login: (username, password) => 
    api.post('/api/auth/login', { username, password }),
};

/**
 * Admin API
 */
export const adminAPI = {
  // Sessions
  getSessions: () => api.get('/admin/sessions'),
  getActiveSessions: () => api.get('/admin/sessions/active'),
  
  // Logs
  getLogs: (params = {}) => api.get('/admin/logs', { params }),
  
  // Metrics
  getMetrics: () => api.get('/admin/metrics'),
  
  // Settings
  getSettings: () => api.get('/admin/settings'),
  updateSetting: (key, value, description) => 
    api.post('/admin/settings', { key, value, description }),
  
  // Health
  healthCheck: () => api.get('/admin/health'),
};

/**
 * WebSocket connection for real-time translation
 */
export class TranslationWebSocket {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.messageHandlers = new Set();
    this.errorHandlers = new Set();
    this.closeHandlers = new Set();
  }

  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_BASE_URL}/ws/translate`);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.messageHandlers.forEach(handler => handler(data));
          } catch (error) {
            console.error('Failed to parse message:', error);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.errorHandlers.forEach(handler => handler(error));
        };
        
        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.closeHandlers.forEach(handler => handler());
          
          // Attempt reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
              console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
              this.connect().catch(console.error);
            }, this.reconnectDelay * this.reconnectAttempts);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  sendConfig(config) {
    if (!this.isConnected) {
      throw new Error('WebSocket not connected');
    }
    
    const message = {
      type: 'config',
      ...config
    };
    
    this.ws.send(JSON.stringify(message));
  }

  sendAudio(audioData) {
    if (!this.isConnected) {
      throw new Error('WebSocket not connected');
    }
    
    this.ws.send(audioData);
  }

  onMessage(handler) {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onError(handler) {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  onClose(handler) {
    this.closeHandlers.add(handler);
    return () => this.closeHandlers.delete(handler);
  }

  disconnect() {
    if (this.ws) {
      this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }
}

export default api;
