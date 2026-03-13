/**
 * Main Translation Page
 * Real-time speech translation interface
 */
import React, { useState, useEffect, useRef } from 'react';
import { publicAPI, TranslationWebSocket } from '../services/api';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import '../styles/TranslationPage.css';

const TranslationPage = () => {
  const [languages, setLanguages] = useState([]);
  const [sourceLang, setSourceLang] = useState('en');
  const [targetLang, setTargetLang] = useState('hi');
  const [isConnected, setIsConnected] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [translations, setTranslations] = useState([]);
  const [error, setError] = useState(null);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [volume, setVolume] = useState(0.8);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [metrics, setMetrics] = useState({ stt: 0, mt: 0, tts: 0 });

  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const translationsEndRef = useRef(null);
  const { isRecording, startRecording, stopRecording, error: recorderError } = useAudioRecorder();

  // Load languages on mount
  useEffect(() => {
    loadLanguages();
  }, []);

  const loadLanguages = async () => {
    try {
      const response = await publicAPI.getLanguages();
      setLanguages(response.data);
      
      // Set default languages if available
      if (response.data.length > 0) {
        const enToHi = response.data.find(l => l.source === 'en' && l.target === 'hi');
        if (enToHi) {
          setSourceLang('en');
          setTargetLang('hi');
        }
      }
    } catch (err) {
      console.error('Failed to load languages:', err);
      setError('Failed to load supported languages');
    }
  };

  const scrollToBottom = () => {
    translationsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [translations]);

  const handleStartTranslation = async () => {
    try {
      setError(null);
      setConnectionStatus('connecting');

      // Create WebSocket connection
      const ws = new TranslationWebSocket();
      wsRef.current = ws;

      // Set up message handler
      ws.onMessage((data) => {
        if (data.type === 'config_ack') {
          setIsConnected(true);
          setConnectionStatus('connected');
          console.log('Configuration acknowledged:', data);
        } else if (data.type === 'translation') {
          // Add translation to list
          setTranslations(prev => [...prev, {
            id: Date.now(),
            sourceText: data.source_text,
            translatedText: data.translated_text,
            timestamp: new Date(data.timestamp),
            isFinal: data.final
          }]);

          // Update metrics
          if (data.stt_time_ms || data.mt_time_ms || data.tts_time_ms) {
            setMetrics({
              stt: data.stt_time_ms || 0,
              mt: data.mt_time_ms || 0,
              tts: data.tts_time_ms || 0
            });
          }

          // Play audio if available
          if (audioEnabled && data.audio) {
            playAudio(data.audio);
          }
        } else if (data.type === 'error') {
          console.error('Translation error:', data.message);
          setError(data.message);
        }
      });

      ws.onError((err) => {
        console.error('WebSocket error:', err);
        setError('Connection error occurred');
        setConnectionStatus('error');
      });

      ws.onClose(() => {
        setIsConnected(false);
        setConnectionStatus('disconnected');
        if (isTranslating) {
          setError('Connection lost');
        }
      });

      // Connect
      await ws.connect();

      // Send configuration
      ws.sendConfig({
        source_lang: sourceLang,
        target_lang: targetLang,
        enable_audio: audioEnabled,
        voice_gender: 'female'
      });

      // Start audio recording
      await startRecording((audioData) => {
        if (ws.isConnected && isTranslating) {
          ws.sendAudio(audioData);
        }
      });

      setIsTranslating(true);
    } catch (err) {
      console.error('Failed to start translation:', err);
      setError(err.message || 'Failed to start translation');
      setConnectionStatus('error');
    }
  };

  const handleStopTranslation = () => {
    setIsTranslating(false);
    stopRecording();
    
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  const playAudio = async (base64Audio) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }

      const audioContext = audioContextRef.current;
      
      // Decode base64 to array buffer
      const binaryString = atob(base64Audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // Decode audio data
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);

      // Create source and gain node
      const source = audioContext.createBufferSource();
      const gainNode = audioContext.createGain();
      
      source.buffer = audioBuffer;
      gainNode.gain.value = volume;
      
      source.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      source.start(0);
    } catch (err) {
      console.error('Failed to play audio:', err);
    }
  };

  const clearTranslations = () => {
    setTranslations([]);
  };

  const getAvailableTargetLanguages = () => {
    return [...new Set(
      languages
        .filter(l => l.source === sourceLang)
        .map(l => ({ code: l.target, name: l.target_name }))
    )];
  };

  const getAvailableSourceLanguages = () => {
    return [...new Set(
      languages.map(l => ({ code: l.source, name: l.source_name }))
    )].filter((v, i, a) => a.findIndex(t => t.code === v.code) === i);
  };

  return (
    <div className="translation-page">
      <div className="translation-container">
        {/* Header */}
        <header className="page-header">
          <div className="header-content">
            <div className="logo-section">
              <div className="logo-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  <path d="M8 10h.01M12 10h.01M16 10h.01" />
                </svg>
              </div>
              <div>
                <h1 className="app-title">Real-Time Translator</h1>
                <p className="app-subtitle">Speak naturally, translate instantly</p>
              </div>
            </div>
            
            <a href="/admin" className="admin-link">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Admin Panel
            </a>
          </div>
        </header>

        {/* Main Content */}
        <main className="main-content">
          {/* Control Panel */}
          <div className="control-panel">
            <div className="language-selectors">
              <div className="language-selector">
                <label>Source Language</label>
                <select 
                  value={sourceLang} 
                  onChange={(e) => setSourceLang(e.target.value)}
                  disabled={isTranslating}
                >
                  {getAvailableSourceLanguages().map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="language-swap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M7 16V4M7 4L3 8M7 4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </div>

              <div className="language-selector">
                <label>Target Language</label>
                <select 
                  value={targetLang} 
                  onChange={(e) => setTargetLang(e.target.value)}
                  disabled={isTranslating}
                >
                  {getAvailableTargetLanguages().map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="control-buttons">
              {!isTranslating ? (
                <button 
                  className="start-button"
                  onClick={handleStartTranslation}
                  disabled={!sourceLang || !targetLang}
                >
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                  </svg>
                  Start Translation
                </button>
              ) : (
                <button 
                  className="stop-button"
                  onClick={handleStopTranslation}
                >
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14H8V8h2v8zm4 0h-2V8h2v8z"/>
                  </svg>
                  Stop Translation
                </button>
              )}

              <button 
                className="clear-button"
                onClick={clearTranslations}
                disabled={translations.length === 0}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Clear
              </button>
            </div>

            <div className="audio-controls">
              <label className="checkbox-label">
                <input 
                  type="checkbox" 
                  checked={audioEnabled}
                  onChange={(e) => setAudioEnabled(e.target.checked)}
                  disabled={isTranslating}
                />
                <span>Enable audio playback</span>
              </label>

              {audioEnabled && (
                <div className="volume-control">
                  <svg viewBox="0 0 24 24" fill="currentColor" className="volume-icon">
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
                  </svg>
                  <input 
                    type="range" 
                    min="0" 
                    max="1" 
                    step="0.1"
                    value={volume}
                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                    className="volume-slider"
                  />
                  <span className="volume-value">{Math.round(volume * 100)}%</span>
                </div>
              )}
            </div>

            {/* Connection Status */}
            <div className={`connection-status status-${connectionStatus}`}>
              <div className="status-indicator"></div>
              <span>
                {connectionStatus === 'disconnected' && 'Disconnected'}
                {connectionStatus === 'connecting' && 'Connecting...'}
                {connectionStatus === 'connected' && 'Connected'}
                {connectionStatus === 'error' && 'Connection Error'}
              </span>
            </div>

            {/* Performance Metrics */}
            {isTranslating && (
              <div className="metrics-display">
                <div className="metric">
                  <span className="metric-label">STT</span>
                  <span className="metric-value">{metrics.stt.toFixed(0)}ms</span>
                </div>
                <div className="metric">
                  <span className="metric-label">MT</span>
                  <span className="metric-value">{metrics.mt.toFixed(0)}ms</span>
                </div>
                <div className="metric">
                  <span className="metric-label">TTS</span>
                  <span className="metric-value">{metrics.tts.toFixed(0)}ms</span>
                </div>
                <div className="metric total">
                  <span className="metric-label">Total</span>
                  <span className="metric-value">{(metrics.stt + metrics.mt + metrics.tts).toFixed(0)}ms</span>
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {(error || recorderError) && (
            <div className="error-banner">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
              </svg>
              <span>{error || recorderError}</span>
            </div>
          )}

          {/* Translations Display */}
          <div className="translations-section">
            <div className="section-header">
              <h2>Translation Stream</h2>
              <span className="translation-count">{translations.length} translations</span>
            </div>

            <div className="translations-list">
              {translations.length === 0 ? (
                <div className="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <p>Translations will appear here in real-time</p>
                  <p className="hint">Click "Start Translation" and begin speaking</p>
                </div>
              ) : (
                <>
                  {translations.map((translation, index) => (
                    <div 
                      key={translation.id} 
                      className={`translation-item ${!translation.isFinal ? 'partial' : ''}`}
                      style={{ animationDelay: `${index * 0.05}s` }}
                    >
                      <div className="translation-time">
                        {translation.timestamp.toLocaleTimeString()}
                      </div>
                      <div className="translation-content">
                        <div className="source-text">
                          <span className="language-tag">{sourceLang.toUpperCase()}</span>
                          {translation.sourceText}
                        </div>
                        <div className="translated-text">
                          <span className="language-tag">{targetLang.toUpperCase()}</span>
                          {translation.translatedText}
                        </div>
                      </div>
                      {!translation.isFinal && (
                        <div className="partial-indicator">Partial</div>
                      )}
                    </div>
                  ))}
                  <div ref={translationsEndRef} />
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default TranslationPage;
