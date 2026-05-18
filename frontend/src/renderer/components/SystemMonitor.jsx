import React, { useState, useEffect, useRef } from 'react';

function SystemMonitor() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [samples, setSamples] = useState([]);
  const [stats, setStats] = useState(null);
  const [wsStatus, setWsStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    checkStatus();
    fetchStats(1);
    const interval = setInterval(checkStatus, 5000);
    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const checkStatus = async () => {
    try {
      const api = window.electronAPI || {
        apiGet: (e) => fetch(`http://127.0.0.1:8472${e}`).then(r => r.json())
      };
      const status = await api.apiGet('/api/telemetry/status');
      setIsMonitoring(status.is_monitoring);
      if (status.is_monitoring && !wsRef.current) {
        connectWebSocket();
      }
    } catch (e) {}
  };

  const connectWebSocket = () => {
    const wsUrl = window.electronAPI?.getWsUrl() || 'ws://127.0.0.1:8472/ws/telemetry';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsStatus('connected');
      ws.send(JSON.stringify({ action: 'get_status' }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'telemetry') {
        setSamples(prev => [...prev.slice(-100), data]);
      }
    };

    ws.onclose = () => {
      setWsStatus('disconnected');
      wsRef.current = null;
    };

    ws.onerror = () => {
      setWsStatus('error');
    };

    wsRef.current = ws;
  };

  const toggleMonitoring = async () => {
    try {
      const api = window.electronAPI || {
        apiPost: (e) => fetch(`http://127.0.0.1:8472${e}`, { method: 'POST' }).then(r => r.json())
      };

      if (isMonitoring) {
        await api.apiPost('/api/telemetry/stop');
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
      } else {
        await api.apiPost('/api/telemetry/start');
        connectWebSocket();
      }
      checkStatus();
    } catch (e) {
      console.error('Toggle monitoring failed:', e);
    }
  };

  const fetchStats = async (hours = 1) => {
    try {
      const api = window.electronAPI || {
        apiGet: (e) => fetch(`http://127.0.0.1:8472${e}`).then(r => r.json())
      };
      const data = await api.apiGet(`/api/telemetry/stats?hours=${hours}`);
      setStats(data);
    } catch (e) {}
  };

  // Simple sparkline SVG
  const Sparkline = ({ data, metric, color, height = 60 }) => {
    if (!data || data.length < 2) return <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No data</div>;

    const values = data.map(d => d?.[metric] ?? 0);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    const points = values.map((v, i) => {
      const x = (i / (values.length - 1)) * 100;
      const y = 100 - ((v - min) / range) * 100;
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: '100%', height, overflow: 'visible' }}>
        <polyline points={points} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
        <defs>
          <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,100 ${points} 100,100`} fill={`url(#grad-${color})`} />
      </svg>
    );
  };

  const currentSample = samples[samples.length - 1];

  return (
    <div>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>System Monitor</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Real-time telemetry and performance tracking</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span className={`status-dot ${isMonitoring ? 'status-online pulse' : 'status-offline'}`}></span>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            {isMonitoring ? 'Monitoring Active' : 'Monitoring Inactive'}
          </span>
          <button className={`btn ${isMonitoring ? 'btn-danger' : 'btn-primary'}`} onClick={toggleMonitoring}>
            {isMonitoring ? 'Stop' : 'Start'} Monitoring
          </button>
        </div>
      </div>

      {/* Live Metrics */}
      <div className="grid grid-4" style={{ marginBottom: '20px' }}>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--primary)' }}>
            {currentSample?.cpu_percent?.toFixed(1) || 0}%
          </div>
          <div className="metric-label">CPU Usage</div>
          <div style={{ marginTop: '8px' }}>
            <Sparkline data={samples} metric="cpu_percent" color="#6366f1" />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--secondary)' }}>
            {currentSample?.memory_percent?.toFixed(1) || 0}%
          </div>
          <div className="metric-label">Memory Usage</div>
          <div style={{ marginTop: '8px' }}>
            <Sparkline data={samples} metric="memory_percent" color="#8b5cf6" />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--info)' }}>
            {currentSample?.gpu_percent?.toFixed(1) || 'N/A'}
          </div>
          <div className="metric-label">GPU Usage</div>
          <div style={{ marginTop: '8px' }}>
            <Sparkline data={samples} metric="gpu_percent" color="#3b82f6" />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-value" style={{ color: 'var(--warning)' }}>
            {currentSample?.temperature_c?.toFixed(1) || 'N/A'}°C
          </div>
          <div className="metric-label">Temperature</div>
          <div style={{ marginTop: '8px' }}>
            <Sparkline data={samples} metric="temperature_c" color="#f59e0b" />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Historical Statistics</h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            {[1, 6, 24].map(h => (
              <button key={h} className="btn btn-secondary" onClick={() => fetchStats(h)} style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
                {h}h
              </button>
            ))}
          </div>
        </div>

        {stats && (
          <div className="grid grid-3">
            {['cpu', 'memory', 'gpu'].map(metric => (
              stats[metric] && (
                <div key={metric} style={{ padding: '16px', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                  <h3 style={{ textTransform: 'uppercase', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                    {metric}
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Avg</div>
                      <div style={{ fontWeight: 600 }}>{stats[metric].avg?.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Min</div>
                      <div style={{ fontWeight: 600 }}>{stats[metric].min?.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Max</div>
                      <div style={{ fontWeight: 600 }}>{stats[metric].max?.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>P95</div>
                      <div style={{ fontWeight: 600 }}>{stats[metric].p95?.toFixed(1)}%</div>
                    </div>
                  </div>
                </div>
              )
            ))}
          </div>
        )}
      </div>

      {/* WebSocket Status */}
      <div style={{ marginTop: '16px', padding: '12px', background: 'var(--bg-tertiary)', borderRadius: '8px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        WebSocket: <span style={{ color: wsStatus === 'connected' ? 'var(--success)' : 'var(--danger)' }}>{wsStatus}</span>
        {' | '}
        Samples: {samples.length}
      </div>
    </div>
  );
}

export default SystemMonitor;
