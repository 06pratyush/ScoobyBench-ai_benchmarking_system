import React, { useState, useEffect } from 'react';
import { apiGet, apiPost, apiUrl } from '../utils/api';

function BenchmarkRunner() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [precision, setPrecision] = useState('fp16');
  const [promptTokens, setPromptTokens] = useState(128);
  const [targetTokens, setTargetTokens] = useState(512);
  const [repeats, setRepeats] = useState(3);
  const [customModelPath, setCustomModelPath] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState({ stage: 'idle', percent: 0 });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const data = await apiGet('/api/models');
      setModels(data);
      if (data.length > 0) setSelectedModel(data[0].id);
    } catch (e) {
      console.error('Failed to fetch models:', e);
    }
  };

  const handleSelectModelFile = async () => {
    if (window.electronAPI) {
      const path = await window.electronAPI.openFile();
      if (path) setCustomModelPath(path);
    }
  };

  const runBenchmark = async () => {
    setIsRunning(true);
    setProgress({ stage: 'preflight', percent: 0 });
    setResult(null);
    setError(null);

    try {
      const modelConfig = {
        name: selectedModel,
        onnx_path: customModelPath || null,
        params_million: models.find(m => m.id === selectedModel)?.params_million || 7000,
        precision: precision,
        batch_size: 1,
        prompt_tokens: parseInt(promptTokens),
        target_tokens: parseInt(targetTokens),
        repeats: parseInt(repeats)
      };

      // Poll for progress
      const progressInterval = setInterval(async () => {
        try {
          const prog = await apiGet(`/api/benchmark/progress/${selectedModel}`);
          setProgress(prog);
        } catch (e) {}
      }, 500);

      const response = await apiPost('/api/benchmark/run', {
        model: modelConfig
      });

      clearInterval(progressInterval);

      if (response.error || response.detail) {
        throw new Error(response.error || response.detail);
      }

      setResult(response);
      setProgress({ stage: 'complete', percent: 100 });
    } catch (e) {
      setError(e.message);
      setProgress({ stage: 'error', percent: 0 });
    } finally {
      setIsRunning(false);
    }
  };

  const abortBenchmark = async () => {
    try {
      await apiPost('/api/benchmark/abort');
    } catch (e) {}
    setIsRunning(false);
  };

  const exportReport = async () => {
    if (!result) return;
    try {
      if (window.electronAPI) {
        const savePath = await window.electronAPI.saveFile(`scoobybench_report_${result.run_id}.json`);
        if (savePath) {
          const report = await apiGet(`/api/benchmark/report/${result.run_id}`);
          await window.electronAPI.writeTextFile(savePath, JSON.stringify(report, null, 2));
        }
      } else {
        window.open(apiUrl(`/api/benchmark/export/${result.run_id}?format=json`));
      }
    } catch (e) {
      console.error('Export failed:', e);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>Benchmark Runner</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Test AI model performance on your hardware</p>
      </div>

      <div className="grid grid-2">
        {/* Configuration */}
        <div className="card">
          <h2 className="card-title">Configuration</h2>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Model
            </label>
            <select 
              className="select" 
              value={selectedModel} 
              onChange={e => setSelectedModel(e.target.value)}
              disabled={isRunning}
            >
              {models.map(m => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.params_million}M params)
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Custom ONNX Model (optional)
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                className="input" 
                value={customModelPath}
                onChange={e => setCustomModelPath(e.target.value)}
                placeholder="Path to .onnx file"
                disabled={isRunning}
                style={{ flex: 1 }}
              />
              <button className="btn btn-secondary" onClick={handleSelectModelFile} disabled={isRunning}>
                Browse
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Precision
              </label>
              <select className="select" value={precision} onChange={e => setPrecision(e.target.value)} disabled={isRunning}>
                <option value="fp32">FP32 (Highest Quality)</option>
                <option value="fp16">FP16 (Balanced)</option>
                <option value="int8">INT8 (Fast)</option>
                <option value="int4">INT4 (Fastest)</option>
              </select>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Prompt Tokens
              </label>
              <input 
                type="number" 
                className="input" 
                value={promptTokens}
                onChange={e => setPromptTokens(e.target.value)}
                min="1" max="4096"
                disabled={isRunning}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Target Tokens
              </label>
              <input 
                type="number" 
                className="input" 
                value={targetTokens}
                onChange={e => setTargetTokens(e.target.value)}
                min="1" max="2048"
                disabled={isRunning}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            {!isRunning ? (
              <button className="btn btn-primary" onClick={runBenchmark} style={{ flex: 1 }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Start Benchmark
              </button>
            ) : (
              <button className="btn btn-danger" onClick={abortBenchmark} style={{ flex: 1 }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                </svg>
                Abort
              </button>
            )}
          </div>
        </div>

        {/* Progress & Results */}
        <div>
          {/* Progress */}
          {isRunning && (
            <div className="card slide-in">
              <h2 className="card-title">Running Benchmark...</h2>
              <div style={{ marginBottom: '8px', textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                Stage: {(progress.stage || 'idle').replace(/_/g, ' ')}
              </div>
              <div className="progress-container">
                <div className="progress-bar" style={{ width: `${progress.percent}%` }}></div>
              </div>
              <div style={{ textAlign: 'right', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                {progress.percent}%
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="alert alert-danger slide-in">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              {error}
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="card slide-in">
              <div className="card-header">
                <h2 className="card-title">Benchmark Results</h2>
                <span className={`grade grade-${result.comparator?.grade?.toLowerCase() || 'b'}`}>
                  {result.comparator?.grade}
                </span>
              </div>

              <div className="grid grid-2" style={{ marginBottom: '16px' }}>
                <div className="metric-card">
                  <div className="metric-value">{result.metrics?.tokens_per_sec?.toFixed(2)}</div>
                  <div className="metric-label">Tokens/sec</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{result.metrics?.latency?.p50_ms?.toFixed(1)}ms</div>
                  <div className="metric-label">P50 Latency</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{result.metrics?.peak_ram_mb?.toFixed(0)}MB</div>
                  <div className="metric-label">Peak RAM</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{result.metrics?.cpu_util_pct?.toFixed(1)}%</div>
                  <div className="metric-label">CPU Util</div>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Comparison</h3>
                <div style={{ 
                  padding: '12px', 
                  background: 'var(--bg-tertiary)', 
                  borderRadius: '8px',
                  border: `1px solid ${result.comparator?.delta_pct > 0 ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Baseline:</span>
                    <span>{result.comparator?.baseline_tokens_per_sec?.toFixed(2)} t/s</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Your Result:</span>
                    <span style={{ fontWeight: 600 }}>{result.metrics?.tokens_per_sec?.toFixed(2)} t/s</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Difference:</span>
                    <span style={{ 
                      color: result.comparator?.delta_pct > 0 ? 'var(--success)' : 'var(--danger)',
                      fontWeight: 600
                    }}>
                      {result.comparator?.delta_pct > 0 ? '+' : ''}{result.comparator?.delta_pct?.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {result.comparator?.probable_causes?.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Detected Issues</h3>
                  {result.comparator.probable_causes.map((cause, i) => (
                    <div key={i} className="alert alert-warning" style={{ marginBottom: '8px' }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                        <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                      </svg>
                      {cause}
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px' }}>
                <button className="btn btn-primary" onClick={exportReport}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Export Report
                </button>
                <button className="btn btn-secondary" onClick={() => setResult(null)}>
                  New Test
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BenchmarkRunner;
