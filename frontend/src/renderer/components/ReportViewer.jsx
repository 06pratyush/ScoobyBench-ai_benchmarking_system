import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiGet, apiUrl } from '../utils/api';

function ReportViewer() {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    fetchReports();
    const reportId = searchParams.get('id');
    if (reportId) {
      fetchReport(reportId);
    }
  }, [searchParams]);

  const fetchReports = async () => {
    try {
      const data = await apiGet('/api/benchmark/reports?limit=50');
      setReports(data);
    } catch (e) {
      console.error('Failed to fetch reports:', e);
    }
  };

  const fetchReport = async (runId) => {
    try {
      const data = await apiGet(`/api/benchmark/report/${runId}`);
      setSelectedReport(data);
    } catch (e) {
      console.error('Failed to fetch report:', e);
    }
  };

  const exportReport = async (runId, format = 'json') => {
    try {
      if (window.electronAPI && format === 'json') {
        const savePath = await window.electronAPI.saveFile(`scoobybench_report_${runId}.json`);
        if (savePath) {
          const report = await apiGet(`/api/benchmark/report/${runId}`);
          await window.electronAPI.writeTextFile(savePath, JSON.stringify(report, null, 2));
        }
      } else {
        window.open(apiUrl(`/api/benchmark/export/${runId}?format=${format}`));
      }
    } catch (e) {
      console.error('Export failed:', e);
    }
  };

  const getGradeClass = (grade) => {
    const map = { 'A': 'grade-a', 'B': 'grade-b', 'C': 'grade-c', 'D': 'grade-d', 'F': 'grade-d' };
    return map[grade] || 'grade-b';
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 700 }}>Benchmark Reports</h1>
        <p style={{ color: 'var(--text-secondary)' }}>View and export your benchmarking history</p>
      </div>

      <div className="grid grid-2">
        {/* Report List */}
        <div className="card" style={{ maxHeight: '70vh', overflow: 'auto' }}>
          <h2 className="card-title">History</h2>
          {reports.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {reports.map(report => (
                <div 
                  key={report.run_id}
                  onClick={() => fetchReport(report.run_id)}
                  style={{
                    padding: '12px',
                    background: selectedReport?.run_id === report.run_id ? 'rgba(99,102,241,0.2)' : 'var(--bg-tertiary)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    border: `1px solid ${selectedReport?.run_id === report.run_id ? 'var(--primary)' : 'transparent'}`
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                        {report.summary?.model?.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        {new Date(report.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <span className={`grade ${getGradeClass(report.summary?.comparator?.grade)}`}>
                      {report.summary?.comparator?.grade}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '0.85rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {report.summary?.metrics?.tokens_per_sec?.toFixed(1)} t/s
                    </span>
                    <span style={{ color: report.summary?.comparator?.delta_pct > 0 ? 'var(--success)' : 'var(--danger)' }}>
                      {report.summary?.comparator?.delta_pct > 0 ? '+' : ''}{report.summary?.comparator?.delta_pct?.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
              <p>No reports yet. Run a benchmark to see results here.</p>
            </div>
          )}
        </div>

        {/* Report Detail */}
        <div>
          {selectedReport ? (
            <div className="card slide-in">
              <div className="card-header">
                <h2 className="card-title">Report Details</h2>
                <span className={`grade ${getGradeClass(selectedReport.comparator?.grade)}`}>
                  {selectedReport.comparator?.grade}
                </span>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Run ID</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>{selectedReport.run_id}</div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Timestamp</div>
                <div>{new Date(selectedReport.timestamp).toLocaleString()}</div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Performance Metrics</h3>
                <div className="grid grid-2">
                  <div className="metric-card" style={{ padding: '12px' }}>
                    <div className="metric-value" style={{ fontSize: '1.5rem' }}>
                      {selectedReport.metrics?.tokens_per_sec?.toFixed(2)}
                    </div>
                    <div className="metric-label">Tokens/sec</div>
                  </div>
                  <div className="metric-card" style={{ padding: '12px' }}>
                    <div className="metric-value" style={{ fontSize: '1.5rem' }}>
                      {selectedReport.metrics?.latency?.p50_ms?.toFixed(1)}ms
                    </div>
                    <div className="metric-label">P50 Latency</div>
                  </div>
                  <div className="metric-card" style={{ padding: '12px' }}>
                    <div className="metric-value" style={{ fontSize: '1.5rem' }}>
                      {selectedReport.metrics?.peak_ram_mb?.toFixed(0)}MB
                    </div>
                    <div className="metric-label">Peak RAM</div>
                  </div>
                  <div className="metric-card" style={{ padding: '12px' }}>
                    <div className="metric-value" style={{ fontSize: '1.5rem' }}>
                      {selectedReport.metrics?.cpu_util_pct?.toFixed(1)}%
                    </div>
                    <div className="metric-label">CPU Utilization</div>
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Latency Distribution</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                  {['p50', 'p90', 'p99'].map(p => (
                    <div key={p} style={{ padding: '10px', background: 'var(--bg-tertiary)', borderRadius: '6px', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{p}</div>
                      <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                        {selectedReport.metrics?.latency?.[`${p}_ms`]?.toFixed(1)}ms
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Comparison</h3>
                <div style={{ padding: '12px', background: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Baseline Source:</span>
                    <span>{selectedReport.comparator?.baseline_source}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Baseline Performance:</span>
                    <span>{selectedReport.comparator?.baseline_tokens_per_sec?.toFixed(2)} t/s</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Your Performance:</span>
                    <span style={{ fontWeight: 600 }}>{selectedReport.metrics?.tokens_per_sec?.toFixed(2)} t/s</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Difference:</span>
                    <span style={{ 
                      color: selectedReport.comparator?.delta_pct > 0 ? 'var(--success)' : 'var(--danger)',
                      fontWeight: 600
                    }}>
                      {selectedReport.comparator?.delta_pct > 0 ? '+' : ''}{selectedReport.comparator?.delta_pct?.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              {selectedReport.comparator?.probable_causes?.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Analysis</h3>
                  {selectedReport.comparator.probable_causes.map((cause, i) => (
                    <div key={i} className="alert alert-warning" style={{ marginBottom: '8px' }}>
                      {cause}
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px' }}>
                <button className="btn btn-primary" onClick={() => exportReport(selectedReport.run_id)}>
                  Export JSON
                </button>
                <button className="btn btn-secondary" onClick={() => setSelectedReport(null)}>
                  Close
                </button>
              </div>
            </div>
          ) : (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
              <p style={{ color: 'var(--text-muted)' }}>Select a report to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportViewer;
