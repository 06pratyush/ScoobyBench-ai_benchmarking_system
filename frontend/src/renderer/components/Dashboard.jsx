import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGet } from '../utils/api';

function Dashboard() {
  const [systemProfile, setSystemProfile] = useState(null);
  const [recentReports, setRecentReports] = useState([]);
  const [telemetryStatus, setTelemetryStatus] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [profile, reports, status, recs] = await Promise.all([
        apiGet('/api/system/profile'),
        apiGet('/api/benchmark/reports?limit=5'),
        apiGet('/api/telemetry/status'),
        apiGet('/api/models/recommendations')
      ]);

      setSystemProfile(profile);
      setRecentReports(reports);
      setTelemetryStatus(status);
      setRecommendations(Array.isArray(recs) ? recs.slice(0, 3) : []);
    } catch (e) {
      console.error('Dashboard fetch error:', e);
      setRecommendations([]);
    }
  };

  const getGradeClass = (grade) => {
    const map = { 'A': 'grade-a', 'B': 'grade-b', 'C': 'grade-c', 'D': 'grade-d', 'F': 'grade-d' };
    return map[grade] || 'grade-b';
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '8px' }}>
          🐕 ScoobyBench Dashboard
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          AI benchmarking and system telemetry for your Windows device
        </p>
      </div>

      {/* System Overview */}
      {systemProfile && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">System Overview</h2>
            <span className={`status-dot ${telemetryStatus?.is_monitoring ? 'status-online' : 'status-offline'}`}>
              {telemetryStatus?.is_monitoring ? 'Monitoring Active' : 'Monitoring Inactive'}
            </span>
          </div>
          <div className="grid grid-4">
            <div className="metric-card">
              <div className="metric-value">{systemProfile.cpu?.name || 'Unknown'}</div>
              <div className="metric-label">CPU</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {systemProfile.cpu?.cores}C / {systemProfile.cpu?.threads}T
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{systemProfile.gpus?.[0]?.name || 'None'}</div>
              <div className="metric-label">GPU</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {systemProfile.gpus?.[0]?.vram_gb ? `${systemProfile.gpus[0].vram_gb}GB VRAM` : 'Integrated'}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{systemProfile.ram?.total_gb}GB</div>
              <div className="metric-label">RAM</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {systemProfile.ram?.available_gb}GB available
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{systemProfile.power_plan}</div>
              <div className="metric-label">Power Plan</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {systemProfile.os}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-2" style={{ marginBottom: '20px' }}>
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: '16px' }}>Quick Actions</h2>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn btn-primary" onClick={() => navigate('/benchmark')}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              Run Benchmark
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/monitor')}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
                <path d="M8 21h8M12 17v4"/>
              </svg>
              Start Monitoring
            </button>
          </div>
        </div>

        <div className="card">
          <h2 className="card-title" style={{ marginBottom: '16px' }}>Recommended Models</h2>
          {recommendations.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recommendations.map(rec => (
                <div key={rec.ai_model_id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px',
                  background: 'var(--bg-tertiary)',
                  borderRadius: '8px',
                  border: rec.compatible ? '1px solid rgba(34,197,94,0.3)' : '1px solid rgba(239,68,68,0.3)'
                }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{rec.ai_model_name}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {rec.reason}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: rec.compatible ? 'var(--success)' : 'var(--danger)' }}>
                      {rec.compatible ? '✓ Compatible' : '✗ Incompatible'}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      ~{rec.estimated_tokens_per_sec} t/s
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>Loading recommendations...</p>
          )}
        </div>
      </div>

      {/* Recent Reports */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Recent Benchmarks</h2>
          <button className="btn btn-secondary" onClick={() => navigate('/reports')}>
            View All
          </button>
        </div>
        {recentReports.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Tokens/sec</th>
                <th>Grade</th>
                <th>Delta</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {recentReports.map(report => (
                <tr key={report.run_id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/reports?id=${report.run_id}`)}>
                  <td style={{ fontWeight: 600 }}>{report.summary?.model?.name}</td>
                  <td>{report.summary?.metrics?.tokens_per_sec?.toFixed(2)}</td>
                  <td>
                    <span className={`grade ${getGradeClass(report.summary?.comparator?.grade)}`}>
                      {report.summary?.comparator?.grade}
                    </span>
                  </td>
                  <td style={{ color: report.summary?.comparator?.delta_pct > 0 ? 'var(--success)' : 'var(--danger)' }}>
                    {report.summary?.comparator?.delta_pct > 0 ? '+' : ''}{report.summary?.comparator?.delta_pct?.toFixed(1)}%
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    {new Date(report.timestamp).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            <p>No benchmarks yet. Run your first test!</p>
            <button className="btn btn-primary" style={{ marginTop: '12px' }} onClick={() => navigate('/benchmark')}>
              Start Benchmark
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
