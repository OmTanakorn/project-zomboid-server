import { useState, useEffect, useRef } from 'react';
import axios, { AxiosError } from 'axios';
import { Users, Box, Terminal, Server, Power, RefreshCw, Trash2, PlusCircle } from 'lucide-react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

interface ServerStatus {
  serverName: string;
  maxPlayers: string;
  onlinePlayers: number;
  playerList: string[];
  status: string;
  version: string;
  modsCount: number;
}

interface Mod {
  id: string;
  workshopId: string;
}

function App() {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('logs');
  const [mods, setMods] = useState<Mod[]>([]);
  const [isActionLoading, setActionLoading] = useState(false);
  const [newMod, setNewMod] = useState({ id: '', workshopId: '' });
  const logEndRef = useRef<HTMLDivElement>(null);

  const fetchData = async () => {
    try {
      const statusRes = await axios.get(`${API_BASE}/status`);
      setStatus(statusRes.data);
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

  const fetchMods = async () => {
    try {
      const res = await axios.get<Mod[]>(`${API_BASE}/mods`);
      setMods(res.data);
    } catch (error) {
      console.error('Error fetching mods:', error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll status more frequently
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === 'logs') {
      fetchLogs();
      const interval = setInterval(fetchLogs, 7000);
      return () => clearInterval(interval);
    } else if (activeTab === 'mods') {
      fetchMods();
    }
  }, [activeTab]);

  const handleServerAction = async (action: 'start' | 'stop' | 'restart') => {
    if (isActionLoading) return;
    setActionLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/server/action/${action}`);
      alert(res.data.message);
      setTimeout(fetchData, 3000); // Refresh status after a delay
    } catch (error) {
      const err = error as AxiosError<{ detail: string }>;
      alert(`Error: ${err.response?.data?.detail || 'An unknown error occurred.'}`);
    } finally {
      setActionLoading(false);
    }
  };
  
  const handleAddMod = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMod.id || !newMod.workshopId) {
      alert('Both Mod ID and Workshop ID are required.');
      return;
    }
    setActionLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/mods`, newMod);
      alert(res.data.message);
      setNewMod({ id: '', workshopId: '' });
      setTimeout(fetchMods, 5000); // Refresh mods after a delay
      setTimeout(fetchData, 5000); // Also refresh server status
    } catch (error) {
      const err = error as AxiosError<{ detail: string }>;
      alert(`Error: ${err.response?.data?.detail || 'An unknown error occurred.'}`);
    } finally {
      setActionLoading(false);
    }
  }
  
  const handleRemoveMod = async (modToRemove: Mod) => {
    if (!confirm(`Are you sure you want to remove the mod "${modToRemove.id}"? The server will restart.`)) return;
    setActionLoading(true);
    try {
      const res = await axios.delete(`${API_BASE}/mods`, { data: modToRemove });
      alert(res.data.message);
      setTimeout(fetchMods, 5000); // Refresh mods after a delay
      setTimeout(fetchData, 5000); // Also refresh server status
    } catch (error) {
      const err = error as AxiosError<{ detail: string }>;
      alert(`Error: ${err.response?.data?.detail || 'An unknown error occurred.'}`);
    } finally {
      setActionLoading(false);
    }
  }

  const getStatusClass = (s: string) => {
    if (s === 'running') return 'status-online';
    if (s === 'restarting' || s === 'starting') return 'status-starting';
    return 'status-offline';
  };

  return (
    <div className="dashboard">
      <header className="header">
        <h1>{status?.serverName || 'Loading...'}</h1>
        <div className="header-right">
          <div className={`status-badge ${getStatusClass(status?.status || '')}`}>
            <div className={`status-dot ${getStatusClass(status?.status || '')}`}></div>
            {status?.status || 'OFFLINE'}
          </div>
          <div className="server-controls">
            <button onClick={() => handleServerAction('start')} disabled={isActionLoading || status?.status === 'running'} title="Start Server">
              <Power size={18} />
              <span>Start</span>
            </button>
            <button onClick={() => handleServerAction('stop')} disabled={isActionLoading || status?.status !== 'running'} className="stop-btn" title="Stop Server">
              <Power size={18} />
              <span>Stop</span>
            </button>
            <button onClick={() => handleServerAction('restart')} disabled={isActionLoading || status?.status !== 'running'} className="restart-btn" title="Restart Server">
              <RefreshCw size={18} />
              <span>Restart</span>
            </button>
          </div>
        </div>
      </header>

      <div className="stats-grid">
        <div className="card">
          <div className="card-title"><Users size={16} /> Players</div>
          <div className="card-value">{status?.onlinePlayers ?? '...'} / {status?.maxPlayers ?? '...'}</div>
          <div className="player-list">
            {status?.playerList && status.playerList.length > 0 ? status.playerList.join(', ') : 'No players online'}
          </div>
        </div>
        <div className="card">
          <div className="card-title"><Box size={16} /> Mods</div>
          <div className="card-value">{status?.modsCount ?? '...'}</div>
        </div>
        <div className="card">
          <div className="card-title"><Server size={16} /> Version</div>
          <div className="card-value">{status?.version || '...'}</div>
        </div>
      </div>

      <div className="tabs">
        <div className={`tab ${activeTab === 'logs' ? 'active' : ''}`} onClick={() => setActiveTab('logs')}><Terminal size={18} /> Logs</div>
        <div className={`tab ${activeTab === 'mods' ? 'active' : ''}`} onClick={() => setActiveTab('mods')}><Box size={18} /> Mod Management</div>
      </div>

      <div className="content">
        {activeTab === 'logs' && (
          <div className="log-container">
            {logs.length > 0 ? logs.map((log, i) => <pre key={i}>{log}</pre>) : <p>Loading logs...</p>}
            <div ref={logEndRef} />
          </div>
        )}

        {activeTab === 'mods' && (
          <>
            <form className="add-mod-form" onSubmit={handleAddMod}>
              <h3><PlusCircle size={20} /> Add New Mod</h3>
              <div className="form-inputs">
                <input 
                  type="text" 
                  placeholder="Mod ID (e.g., firearmmod)" 
                  value={newMod.id}
                  onChange={(e) => setNewMod({...newMod, id: e.target.value})}
                  disabled={isActionLoading}
                />
                <input 
                  type="text" 
                  placeholder="Workshop ID (e.g., 2256623447)" 
                  value={newMod.workshopId}
                  onChange={(e) => setNewMod({...newMod, workshopId: e.target.value})}
                  disabled={isActionLoading}
                />
              </div>
              <button type="submit" disabled={isActionLoading}>
                {isActionLoading ? 'Processing...' : 'Add Mod & Restart'}
              </button>
            </form>
            <div className="mods-list">
              <h3>Installed Mods</h3>
              {mods.map((mod, i) => (
                <div key={i} className="mod-item">
                  <div className="mod-info">
                    <span className="mod-id">{mod.id}</span>
                    <span className="mod-ws-id">Workshop ID: {mod.workshopId}</span>
                  </div>
                  <button onClick={() => handleRemoveMod(mod)} disabled={isActionLoading} className="remove-btn" title={`Remove ${mod.id}`}>
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
