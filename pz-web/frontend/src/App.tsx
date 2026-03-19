import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Users, Terminal, Server, Activity, Cpu, HardDrive } from 'lucide-react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

interface ServerStatus {
  serverName: string;
  maxPlayers: string;
  onlinePlayers: number;
  playerList: string[];
  status: string;
  version: string;
}

interface MonitoringData {
  cpu_percent: number;
  memory_usage_mib: number;
  memory_limit_mib: number;
  memory_percent: number;
  tps: number;
}

function App() {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringData | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  const fetchData = async () => {
    try {
      const [statusRes, monitorRes] = await Promise.all([
        axios.get(`${API_BASE}/status`),
        axios.get(`${API_BASE}/monitoring`).catch(() => ({ data: null }))
      ]);
      setStatus(statusRes.data);
      if (monitorRes.data) setMonitoring(monitorRes.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };
  
  const fetchLogs = async () => {
    try {
      const logsRes = await axios.get(`${API_BASE}/logs`);
      setLogs(logsRes.data.logs);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  }

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000); 
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const getStatusClass = (s: string) => {
    if (s === 'running') return 'status-online';
    if (s === 'restarting' || s === 'starting') return 'status-starting';
    return 'status-offline';
  };

  return (
    <div className="dashboard">
      <header className="header">
        <div className="header-left">
          <Server size={32} className="logo-icon" />
          <div>
            <h1>{status?.serverName || 'Project Zomboid Server'}</h1>
            <p className="version-text">{status?.version || 'Build 42 Unstable'}</p>
          </div>
        </div>
        <div className="header-right">
          <div className={`status-badge ${getStatusClass(status?.status || '')}`}>
            <div className={`status-dot ${getStatusClass(status?.status || '')}`}></div>
            {status?.status?.toUpperCase() || 'OFFLINE'}
          </div>
        </div>
      </header>

      <div className="stats-grid">
        <div className="card">
          <div className="card-header">
            <Users size={18} /> <span>Players Online</span>
          </div>
          <div className="card-content">
            <div className="card-value">{status?.onlinePlayers ?? 0} / {status?.maxPlayers ?? 32}</div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${(status?.onlinePlayers || 0) / parseInt(status?.maxPlayers || '32') * 100}%` }}></div>
            </div>
            <div className="player-list-mini">
              {status?.playerList && status.playerList.length > 0 ? status.playerList.join(', ') : 'No players'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <Cpu size={18} /> <span>CPU Usage</span>
          </div>
          <div className="card-content">
            <div className="card-value">{monitoring?.cpu_percent ?? 0}%</div>
            <div className="progress-bar">
              <div className={`progress-fill ${monitoring?.cpu_percent && monitoring.cpu_percent > 80 ? 'warning' : ''}`} style={{ width: `${monitoring?.cpu_percent ?? 0}%` }}></div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <HardDrive size={18} /> <span>RAM Usage</span>
          </div>
          <div className="card-content">
            <div className="card-value">{monitoring?.memory_usage_mib ? (monitoring.memory_usage_mib / 1024).toFixed(1) : 0} / {(monitoring?.memory_limit_mib ? monitoring.memory_limit_mib / 1024 : 16).toFixed(0)} GB</div>
            <div className="progress-bar">
              <div className={`progress-fill ${monitoring?.memory_percent && monitoring.memory_percent > 80 ? 'warning' : ''}`} style={{ width: `${monitoring?.memory_percent ?? 0}%` }}></div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <Activity size={18} /> <span>Performance</span>
          </div>
          <div className="card-content">
            <div className="card-value">{monitoring?.tps ?? 20} TPS</div>
            <div className="tps-status">
              Target: 20.0 TPS (Stable)
            </div>
          </div>
        </div>
      </div>

      <div className="main-content">
        <div className="tabs">
          <div className="tab-btn active">
            <Terminal size={18} /> Server Logs (Live)
          </div>
        </div>

        <div className="tab-content">
          <div className="log-viewer">
            <div className="log-window">
              {logs.length > 0 ? logs.map((log, i) => (
                <div key={i} className="log-line">
                  <span className="log-index">[{i}]</span> {log}
                </div>
              )) : <div className="loading-text">Fetching logs...</div>}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
