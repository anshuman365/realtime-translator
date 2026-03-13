/**
 * Admin Dashboard Page
 * Control panel for monitoring and managing translation sessions
 */
import React, { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import '../styles/AdminPage.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const AdminDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Filters
  const [logFilters, setLogFilters] = useState({
    source_lang: '',
    target_lang: '',
    status: '',
    limit: 50
  });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [metricsRes, sessionsRes, logsRes, settingsRes] = await Promise.all([
        adminAPI.getMetrics(),
        adminAPI.getActiveSessions(),
        adminAPI.getLogs(logFilters),
        adminAPI.getSettings()
      ]);
      
      setMetrics(metricsRes.data);
      setSessions(sessionsRes.data);
      setLogs(logsRes.data);
      setSettings(settingsRes.data);
      setError(null);
    } catch (err) {
      console.error('Failed to load admin data:', err);
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSetting = async (key, value, description) => {
    try {
      await adminAPI.updateSetting(key, value, description);
      loadData();
    } catch (err) {
      console.error('Failed to update setting:', err);
      alert('Failed to update setting');
    }
  };

  const formatDuration = (startTime, endTime) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end - start) / 1000);
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  if (loading && !metrics) {
    return (
      <div className="admin-page">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="admin-container">
        {/* Header */}
        <header className="admin-header">
          <div className="header-content">
            <div>
              <h1>Admin Control Panel</h1>
              <p>Real-time translation system monitoring and management</p>
            </div>
            <a href="/" className="back-link">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Translator
            </a>
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="error-banner">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Tabs */}
        <div className="admin-tabs">
          <button 
            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`tab ${activeTab === 'sessions' ? 'active' : ''}`}
            onClick={() => setActiveTab('sessions')}
          >
            Sessions
          </button>
          <button 
            className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            Logs
          </button>
          <button 
            className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'overview' && metrics && (
            <div className="overview-tab">
              {/* Metrics Cards */}
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-icon active">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                  </div>
                  <div className="metric-info">
                    <h3>{metrics.active_sessions}</h3>
                    <p>Active Sessions</p>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon sessions">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                    </svg>
                  </div>
                  <div className="metric-info">
                    <h3>{metrics.total_sessions_today}</h3>
                    <p>Sessions Today</p>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon translations">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12.87 15.07l-2.54-2.51.03-.03c1.74-1.94 2.98-4.17 3.71-6.53H17V4h-7V2H8v2H1v1.99h11.17C11.5 7.92 10.44 9.75 9 11.35 8.07 10.32 7.3 9.19 6.69 8h-2c.73 1.63 1.73 3.17 2.98 4.56l-5.09 5.02L4 19l5-5 3.11 3.11.76-2.04zM18.5 10h-2L12 22h2l1.12-3h4.75L21 22h2l-4.5-12zm-2.62 7l1.62-4.33L19.12 17h-3.24z"/>
                    </svg>
                  </div>
                  <div className="metric-info">
                    <h3>{metrics.total_translations_today}</h3>
                    <p>Translations Today</p>
                  </div>
                </div>

                <div className="metric-card">
                  <div className="metric-icon latency">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                    </svg>
                  </div>
                  <div className="metric-info">
                    <h3>{metrics.average_total_latency_ms.toFixed(0)}ms</h3>
                    <p>Avg Total Latency</p>
                  </div>
                </div>
              </div>

              {/* Latency Breakdown */}
              <div className="latency-section">
                <h2>Performance Metrics</h2>
                <div className="latency-bars">
                  <div className="latency-bar-item">
                    <div className="bar-label">
                      <span>STT</span>
                      <span className="bar-value">{metrics.average_stt_latency_ms.toFixed(0)}ms</span>
                    </div>
                    <div className="bar-track">
                      <div 
                        className="bar-fill stt"
                        style={{ width: `${(metrics.average_stt_latency_ms / 1000) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="latency-bar-item">
                    <div className="bar-label">
                      <span>MT</span>
                      <span className="bar-value">{metrics.average_mt_latency_ms.toFixed(0)}ms</span>
                    </div>
                    <div className="bar-track">
                      <div 
                        className="bar-fill mt"
                        style={{ width: `${(metrics.average_mt_latency_ms / 1000) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="latency-bar-item">
                    <div className="bar-label">
                      <span>TTS</span>
                      <span className="bar-value">{metrics.average_tts_latency_ms.toFixed(0)}ms</span>
                    </div>
                    <div className="bar-track">
                      <div 
                        className="bar-fill tts"
                        style={{ width: `${(metrics.average_tts_latency_ms / 1000) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="error-rate">
                  <span className="label">Error Rate:</span>
                  <span className={`value ${metrics.error_rate > 5 ? 'high' : 'low'}`}>
                    {metrics.error_rate.toFixed(2)}%
                  </span>
                </div>
              </div>

              {/* Top Language Pairs */}
              <div className="language-pairs-section">
                <h2>Top Language Pairs (24h)</h2>
                <div className="language-pairs-list">
                  {metrics.top_language_pairs.map((pair, index) => (
                    <div key={index} className="language-pair-item">
                      <div className="pair-info">
                        <span className="pair-languages">
                          {pair.source.toUpperCase()} → {pair.target.toUpperCase()}
                        </span>
                        <span className="pair-count">{pair.count} translations</span>
                      </div>
                      <div className="pair-bar">
                        <div 
                          className="pair-bar-fill"
                          style={{ 
                            width: `${(pair.count / metrics.top_language_pairs[0].count) * 100}%` 
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sessions' && (
            <div className="sessions-tab">
              <div className="section-header">
                <h2>Active Sessions</h2>
                <button onClick={loadData} className="refresh-button">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>

              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Session ID</th>
                      <th>Client IP</th>
                      <th>Languages</th>
                      <th>Started</th>
                      <th>Duration</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="empty-cell">
                          No active sessions
                        </td>
                      </tr>
                    ) : (
                      sessions.map(session => (
                        <tr key={session.id}>
                          <td className="mono">{session.id.substring(0, 8)}</td>
                          <td>{session.client_ip}</td>
                          <td>
                            <span className="language-badge">
                              {session.source_lang} → {session.target_lang}
                            </span>
                          </td>
                          <td>{new Date(session.start_time).toLocaleString()}</td>
                          <td>{formatDuration(session.start_time, session.end_time)}</td>
                          <td>
                            <span className={`status-badge ${session.status}`}>
                              {session.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="logs-tab">
              <div className="section-header">
                <h2>Translation Logs</h2>
                <div className="filter-controls">
                  <select 
                    value={logFilters.status}
                    onChange={(e) => setLogFilters({...logFilters, status: e.target.value})}
                  >
                    <option value="">All Status</option>
                    <option value="success">Success</option>
                    <option value="error">Error</option>
                    <option value="partial">Partial</option>
                  </select>
                  <button onClick={loadData} className="apply-button">Apply</button>
                </div>
              </div>

              <div className="table-container">
                <table className="data-table logs-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Source Text</th>
                      <th>Translated Text</th>
                      <th>Latency</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="empty-cell">
                          No logs found
                        </td>
                      </tr>
                    ) : (
                      logs.map(log => (
                        <tr key={log.id}>
                          <td className="time-cell">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </td>
                          <td className="text-cell">
                            <span className="lang-tag">{log.source_lang}</span>
                            {log.source_text}
                          </td>
                          <td className="text-cell">
                            <span className="lang-tag">{log.target_lang}</span>
                            {log.translated_text}
                          </td>
                          <td className="latency-cell">
                            {log.total_time_ms ? `${log.total_time_ms.toFixed(0)}ms` : 'N/A'}
                          </td>
                          <td>
                            <span className={`status-badge ${log.status}`}>
                              {log.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="settings-tab">
              <h2>System Settings</h2>
              <div className="settings-list">
                {settings.map(setting => (
                  <div key={setting.id} className="setting-item">
                    <div className="setting-info">
                      <h3>{setting.key}</h3>
                      <p>{setting.description || 'No description'}</p>
                    </div>
                    <div className="setting-value">
                      <code>{setting.value}</code>
                    </div>
                  </div>
                ))}
                {settings.length === 0 && (
                  <div className="empty-state">
                    <p>No settings configured</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
