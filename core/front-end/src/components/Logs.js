import React, { useEffect, useState } from 'react';
import './Logs.css';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  const getLogs = async () => {
    try {
      const response = await fetch('http://localhost:5000/logs'); // Endpoint de la API
      if (!response.ok) {
        throw new Error('Error al obtener los logs');
      }
      const data = await response.text(); // Suponemos que los logs son texto
      setLogs(
        data.split('\n')
        .filter((log) => log.trim() !== '')
        .reverse()); // Dividimos por líneas
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    getLogs();
  }, []);

  return (
    <div className="logs-container">
      <h2>Historial de Logs</h2>
      {error ? (
        <p className="error">{error}</p>
      ) : (
        <ul className="logs-list">
          {logs.map((log, index) => (
            <li key={index}>{log}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Logs;
