import React, { useState, useEffect } from 'react';

function Settings() {
  const [config, setConfig] = useState({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const api = window.electronAPI || {
        apiGet: (e) => fetch(`http://127.0.0.1:8472${e}`).then(r => r.json())
      };
      const data = await api.apiGet('/api/config');
      setConfig(data);
    } catch (e) {
      console.error('Failed to fetch config:', e);
    }
  };

  const saveConfig = async () => {
    try {
      const api = window.electronAPI || {
        apiPost: (e, d) => fetch(`http://127.0.0.1:8472${e}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(d)
        }).then(r => r.json())
      };
      await api.apiPost('/api/config', config);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error('Failed to save config:', e);
    }
  };

  const handleChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>Settings</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Configure ScoobyBench behavior and preferences</p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <h2 className="card-title">Telemetry</h2>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Sampling Interval (seconds)
            </label>
            <input 
              type="number" 
              className="input"
              value={config.telemetry_interval || 5}
              onChange={e => handleChange('telemetry_interval', parseFloat(e.target.value))}
              min="1" max="60" step="0.5"
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Data Retention (days)
            </label>
            <input 
              type="number" 
              className="input"
              value={config.telemetry_retention_days || 30}
              onChange={e => handleChange('telemetry_retention_days', parseInt(e.target.value))}
              min="1" max="365"
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Auto-start Monitoring
            </label>
            <select 
              className="select"
              value={config.auto_start_monitor ? 'true' : 'false'}
              onChange={e => handleChange('auto_start_monitor', e.target.value === 'true')}
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </div>
        </div>

        <div className="card">
          <h2 className="card-title">Benchmarking</h2>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Default Repeats
            </label>
            <input 
              type="number" 
              className="input"
              value={config.default_repeats || 3}
              onChange={e => handleChange('default_repeats', parseInt(e.target.value))}
              min="1" max="10"
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Max Test Duration (seconds)
            </label>
            <input 
              type="number" 
              className="input"
              value={config.max_test_duration || 300}
              onChange={e => handleChange('max_test_duration', parseInt(e.target.value))}
              min="60" max="3600"
            />
          </div>
        </div>

        <div className="card">
          <h2 className="card-title">Privacy</h2>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Anonymize Data
            </label>
            <select 
              className="select"
              value={config.anonymize ? 'true' : 'false'}
              onChange={e => handleChange('anonymize', e.target.value === 'true')}
            >
              <option value="true">Yes - Strip PII and hardware serials</option>
              <option value="false">No - Include all system details</option>
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Upload Enabled
            </label>
            <select 
              className="select"
              value={config.upload_enabled ? 'true' : 'false'}
              onChange={e => handleChange('upload_enabled', e.target.value === 'true')}
            >
              <option value="false">No - Keep all data local</option>
              <option value="true">Yes - Allow anonymous uploads</option>
            </select>
          </div>
        </div>

        <div className="card">
          <h2 className="card-title">UI Preferences</h2>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Minimize to Tray
            </label>
            <select 
              className="select"
              value={config.minimize_to_tray ? 'true' : 'false'}
              onChange={e => handleChange('minimize_to_tray', e.target.value === 'true')}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '20px', display: 'flex', gap: '12px', alignItems: 'center' }}>
        <button className="btn btn-primary" onClick={saveConfig}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>
          </svg>
          Save Settings
        </button>
        {saved && (
          <span style={{ color: 'var(--success)', fontSize: '0.9rem' }}>
            ✓ Settings saved successfully
          </span>
        )}
      </div>
    </div>
  );
}

export default Settings;
