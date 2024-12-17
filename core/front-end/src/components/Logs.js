import React, { useEffect, useState } from 'react';
import './Logs.css';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  // Función para obtener los logs
  const getLogs = async () => {
    try {
      const response = await fetch('http://localhost:5000/logs'); // Endpoint de la API
      if (!response.ok) {
        throw new Error('Error al obtener los logs');
      }
      const data = await response.text(); // Suponemos que los logs son texto
      setLogs(
        data
          .split('\n') // Dividimos por líneas
          .filter((log) => log.trim() !== '') // Eliminamos líneas vacías
          .reverse() // Mostramos en orden inverso
      );
      setError(null); // Resetea el error si se obtiene correctamente
    } catch (err) {
      setError(err.message); // Captura y muestra el error
    }
  };

  // Efecto que actualiza los logs cada segundo
  useEffect(() => {
    getLogs(); // Llamada inicial
    const interval = setInterval(getLogs, 1000); // Repetir cada 1 segundo
    return () => clearInterval(interval); // Limpiar el intervalo al desmontar el componente
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
