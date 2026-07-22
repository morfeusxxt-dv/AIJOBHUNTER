import React, { useState, useEffect } from 'react';
import './App.css';

interface StatData {
  total_jobs: number;
  total_analyzed: number;
  total_applied: number;
  average_score: number;
  daily_applies: number;
  top_technologies: { name: string; count: number }[];
}

interface Job {
  id: number;
  title: string;
  location: string;
  url: string;
  easy_apply: boolean;
  level: string;
  status: string;
  score: number | null;
  created_at: string;
  company: { name: string; blocked: boolean };
}

interface Settings {
  keywords: string[];
  locations: string[];
  remote: boolean;
  hybrid: boolean;
  onsite: boolean;
  score_min: number;
  daily_max: number;
  allowed_hours_start: number;
  allowed_hours_end: number;
}

interface LogEntry {
  id: number;
  service: string;
  message: string;
  level: string;
  created_at: string;
}

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'queue' | 'settings' | 'logs' | 'auth'>('dashboard');
  
  // Dashboard state
  const [stats, setStats] = useState<StatData>({
    total_jobs: 0,
    total_analyzed: 0,
    total_applied: 0,
    average_score: 0,
    daily_applies: 0,
    top_technologies: []
  });
  
  // Jobs/Queue state
  const [jobs, setJobs] = useState<Job[]>([]);
  
  // Logs state
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  // Settings state
  const [config, setConfig] = useState<Settings>({
    keywords: [],
    locations: [],
    remote: true,
    hybrid: false,
    onsite: false,
    score_min: 90,
    daily_max: 15,
    allowed_hours_start: 9,
    allowed_hours_end: 18
  });
  
  // Input fields for settings lists
  const [newKeyword, setNewKeyword] = useState('');
  const [newLocation, setNewLocation] = useState('');

  // Authentication state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [authStatus, setAuthStatus] = useState('');

  const API_BASE = 'http://localhost:8000/api/v1';

  // Fetch Stats & Logs
  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard/stats`);
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs/queue`);
      if (res.ok) setJobs(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/logs`);
      if (res.ok) setLogs(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/settings`);
      if (res.ok) setConfig(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchJobs();
    fetchLogs();
    fetchSettings();

    const interval = setInterval(() => {
      fetchStats();
      fetchJobs();
      fetchLogs();
    }, 10000); // refresh every 10s

    return () => clearInterval(interval);
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (res.ok) {
        alert('Settings saved successfully!');
        fetchSettings();
      }
    } catch (e) {
      alert('Error saving settings.');
    }
  };

  const handleLinkedInLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthStatus('Logging in... (Wait up to 30s)');
    try {
      const res = await fetch(`${API_BASE}/settings/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (res.ok) {
        setAuthStatus('Login Success! Cookies saved securely.');
        setUsername('');
        setPassword('');
        fetchLogs();
      } else {
        setAuthStatus(`Login Failed: ${data.detail || 'check logs'}`);
      }
    } catch (err) {
      setAuthStatus('Network error during login.');
    }
  };

  const triggerCrawl = async () => {
    try {
      await fetch(`${API_BASE}/jobs/trigger/crawl`, { method: 'POST' });
      alert('LinkedIn Crawler workflow initiated in the background.');
      fetchLogs();
    } catch (e) {
      console.error(e);
    }
  };

  const triggerApply = async () => {
    try {
      await fetch(`${API_BASE}/jobs/trigger/apply`, { method: 'POST' });
      alert('LinkedIn Easy Apply workflow initiated in the background.');
      fetchLogs();
    } catch (e) {
      console.error(e);
    }
  };

  const addKeyword = () => {
    if (newKeyword.trim() && !config.keywords.includes(newKeyword.trim())) {
      setConfig({ ...config, keywords: [...config.keywords, newKeyword.trim()] });
      setNewKeyword('');
    }
  };

  const removeKeyword = (kw: string) => {
    setConfig({ ...config, keywords: config.keywords.filter(k => k !== kw) });
  };

  const addLocation = () => {
    if (newLocation.trim() && !config.locations.includes(newLocation.trim())) {
      setConfig({ ...config, locations: [...config.locations, newLocation.trim()] });
      setNewLocation('');
    }
  };

  const removeLocation = (loc: string) => {
    setConfig({ ...config, locations: config.locations.filter(l => l !== loc) });
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div>
          <div className="brand">
            <span className="brand-logo">JobHunter.ai</span>
          </div>
          
          <ul className="nav-links">
            <li 
              className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              📊 Dashboard
            </li>
            <li 
              className={`nav-item ${activeTab === 'queue' ? 'active' : ''}`}
              onClick={() => setActiveTab('queue')}
            >
              📋 Job Queue
            </li>
            <li 
              className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              ⚙️ Settings
            </li>
            <li 
              className={`nav-item ${activeTab === 'logs' ? 'active' : ''}`}
              onClick={() => setActiveTab('logs')}
            >
              🖥️ Live Logs
            </li>
            <li 
              className={`nav-item ${activeTab === 'auth' ? 'active' : ''}`}
              onClick={() => setActiveTab('auth')}
            >
              🔑 LinkedIn Connect
            </li>
          </ul>
        </div>
        
        <div style={{ color: 'var(--color-muted)', fontSize: '0.8rem' }}>
          v1.0.0 Stable Release
        </div>
      </aside>

      {/* Main Panel Content */}
      <main className="main-content">
        <header className="header">
          <div>
            <h1 className="page-title">
              {activeTab === 'dashboard' && 'Dashboard Overview'}
              {activeTab === 'queue' && 'Application Queue'}
              {activeTab === 'settings' && 'System Parameters'}
              {activeTab === 'logs' && 'Audit Logs Console'}
              {activeTab === 'auth' && 'LinkedIn Authentication'}
            </h1>
            <p style={{ color: 'var(--color-muted)', fontSize: '0.9rem' }}>
              Autonomic job parsing and Easy Apply workflows
            </p>
          </div>

          <div className="action-buttons">
            <button className="btn-secondary" onClick={triggerCrawl}>🕷️ Crawl Now</button>
            <button className="btn-primary" onClick={triggerApply}>🚀 Apply Now</button>
          </div>
        </header>

        {/* Tab contents */}
        {activeTab === 'dashboard' && (
          <div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Scraped</div>
                <div className="stat-value">{stats.total_jobs}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Jobs Analyzed</div>
                <div className="stat-value">{stats.total_analyzed}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Applied</div>
                <div className="stat-value" style={{ color: 'var(--color-success)' }}>
                  {stats.total_applied}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg Compatibility Score</div>
                <div className="stat-value" style={{ color: 'var(--color-secondary)' }}>
                  {stats.average_score}%
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Daily Applies ({stats.daily_applies}/{config.daily_max})</div>
                <div className="stat-value">
                  {stats.daily_applies}
                </div>
              </div>
            </div>

            <div className="table-container" style={{ marginTop: '2rem' }}>
              <h2 style={{ marginBottom: '1.5rem', fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>
                🔥 Target Technologies Distribution
              </h2>
              <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                {stats.top_technologies.map(t => (
                  <div 
                    key={t.name}
                    style={{
                      background: 'rgba(255, 255, 255, 0.03)',
                      padding: '1rem 1.5rem',
                      borderRadius: '12px',
                      border: '1px solid var(--border-glass)'
                    }}
                  >
                    <span style={{ fontWeight: '600', marginRight: '0.5rem' }}>{t.name.toUpperCase()}</span>
                    <span style={{ color: 'var(--color-secondary)' }}>({t.count} jobs)</span>
                  </div>
                ))}
                {stats.top_technologies.length === 0 && <p style={{ color: 'var(--color-muted)' }}>No tags found yet.</p>}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'queue' && (
          <div className="table-container">
            <table className="premium-table">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Company</th>
                  <th>Location</th>
                  <th>Easy Apply</th>
                  <th>Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr key={job.id}>
                    <td>
                      <a href={job.url} target="_blank" rel="noreferrer" style={{ color: 'var(--color-text-bright)', textDecoration: 'none', fontWeight: '500' }}>
                        {job.title}
                      </a>
                    </td>
                    <td>{job.company.name}</td>
                    <td>{job.location}</td>
                    <td>{job.easy_apply ? '🟢 Yes' : '🔴 No'}</td>
                    <td>
                      <span style={{ fontWeight: 'bold', color: (job.score || 0) >= 90 ? 'var(--color-success)' : 'var(--color-muted)' }}>
                        {job.score !== null ? `${job.score}%` : 'N/A'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${job.status.toLowerCase()}`}>
                        {job.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {jobs.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', color: 'var(--color-muted)' }}>
                      No jobs currently in queue.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'settings' && (
          <form className="settings-form" onSubmit={handleSaveSettings}>
            <div className="form-group full-width">
              <label>Target Keywords</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input 
                  type="text" 
                  value={newKeyword} 
                  onChange={e => setNewKeyword(e.target.value)} 
                  placeholder="e.g. FastAPI"
                />
                <button type="button" className="btn-secondary" onClick={addKeyword}>Add</button>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                {config.keywords.map(kw => (
                  <span 
                    key={kw} 
                    style={{ background: 'var(--color-primary-glow)', padding: '0.25rem 0.75rem', borderRadius: '20px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                  >
                    {kw}
                    <button type="button" style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }} onClick={() => removeKeyword(kw)}>x</button>
                  </span>
                ))}
              </div>
            </div>

            <div className="form-group full-width">
              <label>Target Locations</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input 
                  type="text" 
                  value={newLocation} 
                  onChange={e => setNewLocation(e.target.value)} 
                  placeholder="e.g. Remote"
                />
                <button type="button" className="btn-secondary" onClick={addLocation}>Add</button>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                {config.locations.map(loc => (
                  <span 
                    key={loc} 
                    style={{ background: 'var(--color-secondary-glow)', padding: '0.25rem 0.75rem', borderRadius: '20px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                  >
                    {loc}
                    <button type="button" style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }} onClick={() => removeLocation(loc)}>x</button>
                  </span>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Work Modality</label>
              <div className="checkbox-group">
                <label className="checkbox-item">
                  <input type="checkbox" checked={config.remote} onChange={e => setConfig({ ...config, remote: e.target.checked })} />
                  Remote
                </label>
                <label className="checkbox-item">
                  <input type="checkbox" checked={config.hybrid} onChange={e => setConfig({ ...config, hybrid: e.target.checked })} />
                  Hybrid
                </label>
                <label className="checkbox-item">
                  <input type="checkbox" checked={config.onsite} onChange={e => setConfig({ ...config, onsite: e.target.checked })} />
                  Onsite
                </label>
              </div>
            </div>

            <div className="form-group">
              <label>Min Compatibility Score (%)</label>
              <input 
                type="number" 
                value={config.score_min} 
                onChange={e => setConfig({ ...config, score_min: parseInt(e.target.value) || 90 })} 
              />
            </div>

            <div className="form-group">
              <label>Max Daily Applications Limit</label>
              <input 
                type="number" 
                value={config.daily_max} 
                onChange={e => setConfig({ ...config, daily_max: parseInt(e.target.value) || 15 })} 
              />
            </div>

            <div className="form-group">
              <label>Allowed Apply Hours Window</label>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input 
                  type="number" 
                  value={config.allowed_hours_start} 
                  style={{ width: '80px' }}
                  onChange={e => setConfig({ ...config, allowed_hours_start: parseInt(e.target.value) || 0 })} 
                  placeholder="Start"
                />
                <span>to</span>
                <input 
                  type="number" 
                  value={config.allowed_hours_end} 
                  style={{ width: '80px' }}
                  onChange={e => setConfig({ ...config, allowed_hours_end: parseInt(e.target.value) || 24 })} 
                  placeholder="End"
                />
                <span>H</span>
              </div>
            </div>

            <div className="submit-container">
              <button type="submit" className="btn-primary">Save Settings</button>
            </div>
          </form>
        )}

        {activeTab === 'logs' && (
          <div className="terminal-container">
            {logs.map(log => (
              <div key={log.id} className={`terminal-line ${log.level.toLowerCase()}`}>
                <span className="timestamp">[{new Date(log.created_at).toLocaleTimeString()}]</span>
                <span className="service">{log.service.toUpperCase()}:</span>
                {log.message}
              </div>
            ))}
            {logs.length === 0 && <div className="terminal-line">Listening for logs...</div>}
          </div>
        )}

        {activeTab === 'auth' && (
          <div className="table-container" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <h2 style={{ marginBottom: '1.5rem', fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>
              🔑 Secure LinkedIn Connect
            </h2>
            <p style={{ color: 'var(--color-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              We simulate a headless/headful login workflow to extract secure authentication cookies. 
              Passwords are encrypted symmetrically using AES (Fernet) before storing.
            </p>
            <form onSubmit={handleLinkedInLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="form-group">
                <label>LinkedIn Email / Username</label>
                <input 
                  type="text" 
                  value={username} 
                  onChange={e => setUsername(e.target.value)} 
                  placeholder="name@email.com" 
                  required
                />
              </div>
              <div className="form-group">
                <label>LinkedIn Password</label>
                <input 
                  type="password" 
                  value={password} 
                  onChange={e => setPassword(e.target.value)} 
                  placeholder="••••••••" 
                  required
                />
              </div>
              <button type="submit" className="btn-primary" style={{ alignSelf: 'flex-end', marginTop: '1rem' }}>
                Establish LinkedIn Session
              </button>
            </form>
            {authStatus && (
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.9rem' }}>
                {authStatus}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
