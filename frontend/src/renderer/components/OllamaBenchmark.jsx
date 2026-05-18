import React, { useState, useEffect } from 'react';

function OllamaBenchmark() {
  const [ollamaStatus, setOllamaStatus] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [prompt, setPrompt] = useState('Explain quantum computing in simple terms.');
  const [maxTokens, setMaxTokens] = useState(256);
  const [repeats, setRepeats] = useState(3);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [pullModelName, setPullModelName] = useState('');
  const [isPulling, setIsPulling] = useState(false);

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkStatus = async () => {
    try {
      const api = window.electronAPI || {
        apiGet: (e) => fetch(`http://127.0.0.1:8472${e}`).then(r => r.json())
      };
      const status = await api.apiGet('/api/ollama/status');
      setOllamaStatus(status);

      if (status.available) {
        const modelsData = await api.apiGet('/api/ollama/models');
        if (modelsData.models) {
          setModels(modelsData.models);
          if (modelsData.models.length > 0 && !selectedModel) {
            setSelectedModel(modelsData.models[0].name);
          }
        }
      }
    } catch (e) {
      console.error('Ollama status check failed:', e);
      setOllamaStatus({ available: false });
    }
  };

  const runBenchmark = async () => {
    setIsRunning(true);
    setResult(null);
    setError(null);

    try {
      const api = window.electronAPI || {
        apiPost: (e, d) => fetch(`http://127.0.0.1:8472${e}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(d)
        }).then(r => r.json())
      };

      const response = await api.apiPost('/api/ollama/benchmark', {
        model_name: selectedModel,
        prompt: prompt,
        max_tokens: parseInt(maxTokens),
        repeats: parseInt(repeats)
      });

      if (response.error || response.detail) {
        throw new Error(response.error || response.detail);
      }

      setResult(response);
    } catch (e) {
      setError(e.message);
    } finally {
      setIsRunning(false);
    }
  };

  const pullModel = async () => {
    if (!pullModelName.trim()) return;
    setIsPulling(true);
    setError(null);

    try {
      const api = window.electronAPI || {
        apiPost: (e) => fetch(`http://127.0.0.1:8472${e}`, { method: 'POST' }).then(r => r.json())
      };
      const response = await api.apiPost(`/api/ollama/pull/${pullModelName.trim()}`);

      if (response.success) {
        alert(`Model ${pullModelName} pulled successfully!`);
        checkStatus();
      } else {
        setError(`Failed to pull ${pullModelName}`);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setIsPulling(false);
    }
  };

  const getGradeClass = (grade) => {
    const map = { 'A': 'grade-a', 'B': 'grade-b', 'C': 'grade-c', 'D': 'grade-d', 'F': 'grade-d' };
    return map[grade] || 'grade-b';
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>Ollama Benchmark</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Benchmark locally-running Ollama models (llama3, gemma, phi, etc.)
        </p>
      </div>

      {/* Ollama Status */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card-header">
          <h2 className="card-title">Ollama Status</h2>
          <span className={`status-dot ${ollamaStatus?.available ? 'status-online' : 'status-offline'}`}></span>
        </div>

        {ollamaStatus?.available ? (
          <div style={{ color: 'var(--success)' }}>
            Ollama is running at {ollamaStatus.host} (v{ollamaStatus.version})
          </div>
        ) : (
          <div>
            <div className="alert alert-danger" style={{ marginBottom: '12px' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              Ollama is not running. Install and start it:
              <pre style={{ marginTop: '8px', padding: '10px', background: 'var(--bg-tertiary)', borderRadius: '6px', fontSize: '0.85rem' }}>
{`# Install: https://ollama.com/download
# Then run:
ollama serve`}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Pull Model */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h2 className="card-title">Pull Model</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '12px', fontSize: '0.9rem' }}>
          Download a model from Ollama registry (e.g., gemma, llama3, phi3)
        </p>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input 
            type="text" 
            className="input"
            value={pullModelName}
            onChange={e => setPullModelName(e.target.value)}
            placeholder="e.g., gemma:2b or llama3"
            style={{ flex: 1 }}
          />
          <button 
            className="btn btn-secondary" 
            onClick={pullModel}
            disabled={isPulling || !pullModelName.trim()}
          >
            {isPulling ? 'Pulling...' : 'Pull'}
          </button>
        </div>
      </div>

      <div className="grid grid-2">
        {/* Configuration */}
        <div className="card">
          <h2 className="card-title">Configuration</h2>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Model ({models.length} available)
            </label>
            <select 
              className="select" 
              value={selectedModel} 
              onChange={e => setSelectedModel(e.target.value)}
              disabled={isRunning || !ollamaStatus?.available}
            >
              {models.map(m => (
                <option key={m.name} value={m.name}>
                  {m.name} ({m.parameter_size}, {m.quantization_level}, {m.size_gb}GB)
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Prompt
            </label>
            <textarea 
              className="input" 
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              rows={3}
              disabled={isRunning}
              style={{ resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Max Tokens
              </label>
              <input 
                type="number" 
                className="input" 
                value={maxTokens}
                onChange={e => setMaxTokens(e.target.value)}
                min="1" max="2048"
                disabled={isRunning}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Repeats
              </label>
              <input 
                type="number" 
                className="input" 
                value={repeats}
                onChange={e => setRepeats(e.target.value)}
                min="1" max="10"
                disabled={isRunning}
              />
            </div>
          </div>

          <button 
            className="btn btn-primary" 
            onClick={runBenchmark} 
            disabled={isRunning || !ollamaStatus?.available || !selectedModel}
            style={{ width: '100%' }}
          >
            {isRunning ? 'Running...' : 'Start Ollama Benchmark'}
          </button>
        </div>

        {/* Results */}
        <div>
          {error && (
            <div className="alert alert-danger slide-in">
              {error}
            </div>
          )}

          {result && (
            <div className="card slide-in">
              <div className="card-header">
                <h2 className="card-title">Ollama Results</h2>
                <span className={`grade ${getGradeClass(result.comparator?.grade)}`}>
                  {result.comparator?.grade}
                </span>
              </div>

              <div className="grid grid-2" style={{ marginBottom: '16px' }}>
                <div className="metric-card">
                  <div className="metric-value">{(result.metrics?.tokens_per_sec || 0).toFixed(2)}</div>
                  <div className="metric-label">Tokens/sec</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{(result.metrics?.latency?.p50_ms || 0).toFixed(1)}ms</div>
                  <div className="metric-label">P50 Latency</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{(result.metrics?.peak_ram_mb || 0).toFixed(0)}MB</div>
                  <div className="metric-label">Peak RAM</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{(result.metrics?.cpu_util_pct || 0).toFixed(1)}%</div>
                  <div className="metric-label">CPU Util</div>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Comparison</h3>
                <div style={{ padding: '12px', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Baseline:</span>
                    <span>{(result.comparator?.baseline_tokens_per_sec || 0).toFixed(2)} t/s</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Your Result:</span>
                    <span style={{ fontWeight: 600 }}>{(result.metrics?.tokens_per_sec || 0).toFixed(2)} t/s</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Difference:</span>
                    <span style={{ 
                      color: (result.comparator?.delta_pct || 0) > 0 ? 'var(--success)' : 'var(--danger)',
                      fontWeight: 600
                    }}>
                      {(result.comparator?.delta_pct || 0) > 0 ? '+' : ''}{(result.comparator?.delta_pct || 0).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {result.environment_snapshot?.model_info && (
                <div style={{ marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Model Info</h3>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                    <div>Family: {result.environment_snapshot.model_info.family}</div>
                    <div>Format: {result.environment_snapshot.model_info.format}</div>
                    <div>Quantization: {result.environment_snapshot.model_info.quantization_level}</div>
                    <div>Size: {result.environment_snapshot.model_info.size_gb}GB</div>
                  </div>
                </div>
              )}

              <button className="btn btn-secondary" onClick={() => setResult(null)}>
                New Test
              </button>
            </div>
          )}

          {!result && !error && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '200px' }}>
              <p style={{ color: 'var(--text-muted)' }}>
                {ollamaStatus?.available 
                  ? 'Select a model and click Start Benchmark' 
                  : 'Start Ollama to see models'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default OllamaBenchmark;
