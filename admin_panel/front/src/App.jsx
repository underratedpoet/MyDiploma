import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend
} from 'recharts';

const BACKEND = "http://localhost:5000";

export default function App() {
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [metrics, setMetrics] = useState([]);
  const [logs, setLogs] = useState({});
  const [selected, setSelected] = useState(null);

  const fetchMetrics = () => {
    axios.get(`${BACKEND}/metrics`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => setMetrics(res.data));
  };

  const fetchLogs = (name) => {
    axios.get(`${BACKEND}/logs/${name}`, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => {
      setLogs(l => ({ ...l, [name]: res.data.logs }));
    });
  };

  const login = () => {
    axios.post(`${BACKEND}/auth`, { password }, {
      headers: { 'Content-Type': 'application/json' }
    }).then(res => {
      if (res.data.success) {
        setToken(password);
        fetchMetrics();
      }
    });
  };

  useEffect(() => {
    const interval = setInterval(() => {
      if (token) fetchMetrics();
    }, 5000);
    return () => clearInterval(interval);
  }, [token]);

  if (!token) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', height: '100vh', fontFamily: 'sans-serif'
      }}>
        <h2>🔐 Admin Panel</h2>
        <input
          placeholder="Введите пароль"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ padding: '8px', marginBottom: '10px', width: '200px' }}
        />
        <button onClick={login} style={{ padding: '8px 16px', cursor: 'pointer' }}>
          Войти
        </button>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '20px' }}>
      <h1 style={{ marginBottom: '20px' }}>📊 Docker Admin Panel</h1>

      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '20px',
        minHeight: '500px'
      }}>
        {/* Контейнеры */}
        <div style={{
          flex: '0 0 300px',
          border: '1px solid #ccc',
          borderRadius: '8px',
          padding: '10px',
          background: '#f9f9f9',
          overflowY: 'auto',
          maxHeight: '600px'
        }}>
          <h3>Контейнеры</h3>
          {metrics.map(c => (
            <div
              key={c.name}
              style={{
                borderBottom: '1px solid #ddd',
                padding: '10px 0',
                cursor: 'pointer'
              }}
              onClick={() => {
                setSelected(c.name);
                fetchLogs(c.name);
              }}
            >
              <b>{c.name}</b> <span style={{ color: '#666' }}>({c.status})</span>
              <br />
              CPU: {c.cpu_total} <br />
              Mem: {(c.memory_usage / 1024 / 1024).toFixed(2)} MB
            </div>
          ))}
        </div>

        {/* Логи */}
        <div style={{
          flex: 1,
          border: '1px solid #ccc',
          borderRadius: '8px',
          padding: '10px',
          background: '#fff',
          minHeight: '600px'
        }}>
          <h3>Логи</h3>
          {selected ? (
            <div>
              <div style={{
                marginBottom: '8px',
                fontWeight: 'bold',
                borderBottom: '1px solid #eee',
                paddingBottom: '5px'
              }}>
                {selected}
              </div>
              <pre style={{
                background: '#111',
                color: '#0f0',
                padding: '10px',
                height: '500px',
                overflowY: 'scroll',
                fontSize: '12px',
                borderRadius: '4px'
              }}>
                {(logs[selected] || []).join('\n')}
              </pre>
            </div>
          ) : (
            <div>Выберите контейнер для просмотра логов</div>
          )}
        </div>
      </div>

      {/* График */}
      <div style={{ marginTop: '40px' }}>
        <h3>Использование памяти (MB)</h3>
        <BarChart width={900} height={300} data={metrics.map(m => ({
          name: m.name,
          memory: +(m.memory_usage / 1024 / 1024).toFixed(2)
        }))}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="memory" fill="#82ca9d" />
        </BarChart>
      </div>
    </div>
  );
}
