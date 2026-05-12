import React, { useState, useEffect } from 'react';

function ModelBrowser() {
  const [models, setModels] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const api = window.electronAPI || {
        apiGet: (e) => fetch(`http://127.0.0.1:8472${e}`).then(r => r.json())
      };
      const [modelsData, recsData] = await Promise.all([
        api.apiGet('/api/models'),
        api.apiGet('/api/models/recommendations')
      ]);
      setModels(modelsData);
      setRecommendations(recsData);
    } catch (e) {
      console.error('Failed to fetch models:', e);
    }
  };

  const filteredModels = models.filter(m => 
    m.name.toLowerCase().includes(filter.toLowerCase()) ||
    m.tags.some(t => t.toLowerCase().includes(filter.toLowerCase()))
  );

  const getRecForModel = (modelId) => recommendations.find(r => r.ai_model_id === modelId);

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>Model Browser</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Discover AI models compatible with your hardware</p>
      </div>

      <div className="card" style={{ marginBottom: '20px' }}>
        <input 
          type="text" 
          className="input" 
          placeholder="Search models by name or tag..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
        />
      </div>

      <div className="grid grid-2">
        {filteredModels.map(model => {
          const rec = getRecForModel(model.id);
          return (
            <div 
              key={model.id} 
              className="card" 
              style={{ 
                cursor: 'pointer',
                border: selectedModel?.id === model.id ? '2px solid var(--primary)' : undefined
              }}
              onClick={() => setSelectedModel(model)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '4px' }}>{model.name}</h3>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    {model.params_million}M parameters
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  {model.tags.map(tag => (
                    <span key={tag} style={{ 
                      fontSize: '0.75rem', 
                      padding: '4px 8px', 
                      background: 'var(--bg-tertiary)',
                      borderRadius: '4px',
                      color: 'var(--text-secondary)'
                    }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                {model.description}
              </p>

              <div style={{ display: 'flex', gap: '16px', fontSize: '0.85rem', marginBottom: '12px' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Min RAM: </span>
                  <span style={{ fontWeight: 600 }}>{model.min_ram_gb}GB</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Min VRAM: </span>
                  <span style={{ fontWeight: 600 }}>{model.min_vram_gb || 'N/A'}GB</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Precision: </span>
                  <span style={{ fontWeight: 600 }}>{model.recommended_precision.toUpperCase()}</span>
                </div>
              </div>

              {rec && (
                <div style={{ 
                  padding: '10px', 
                  background: rec.compatible ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                  borderRadius: '6px',
                  border: `1px solid ${rec.compatible ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.9rem', color: rec.compatible ? 'var(--success)' : 'var(--danger)' }}>
                      {rec.compatible ? '✓ Compatible' : '✗ Incompatible'}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Confidence: {Math.round(rec.confidence * 100)}%
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {rec.reason}
                  </div>
                  {rec.compatible && (
                    <div style={{ fontSize: '0.85rem', marginTop: '4px' }}>
                      Est. performance: ~{rec.estimated_tokens_per_sec} tokens/sec
                    </div>
                  )}
                </div>
              )}

              <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
                <button className="btn btn-primary" style={{ flex: 1, padding: '8px' }} onClick={(e) => {
                  e.stopPropagation();
                  window.location.hash = '/benchmark';
                }}>
                  Benchmark
                </button>
                {model.huggingface_id && (
                  <button className="btn btn-secondary" style={{ padding: '8px' }} onClick={(e) => {
                    e.stopPropagation();
                    if (window.electronAPI) {
                      window.electronAPI.openExternal(`https://huggingface.co/${model.huggingface_id}`);
                    }
                  }}>
                    HuggingFace
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ModelBrowser;
