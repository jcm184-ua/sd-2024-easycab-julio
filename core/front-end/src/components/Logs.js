import React, { useEffect, useState } from 'react';
import './Logs.css';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [maxLogs, setMaxLogs] = useState(50); // Estado para el número máximo de logs
  const [inputValue, setInputValue] = useState(50); // Estado para el input del formulario

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
          .slice(0, maxLogs) // Limitamos el número de logs al valor definido
      );
      setError(null); // Resetea el error si se obtiene correctamente
    } catch (err) {
      setError('Error al conectarse a la central: ' + err); // Captura y muestra el error
    }
  };

  // Efecto que actualiza los logs cada segundo
  useEffect(() => {
    getLogs(); // Llamada inicial
    const interval = setInterval(getLogs, 1000); // Repetir cada 1 segundo
    return () => clearInterval(interval); // Limpiar el intervalo al desmontar el componente
  }, [maxLogs]); // Ejecutar nuevamente cuando cambie el valor de maxLogs

  // Manejar el cambio de número máximo de logs
  const handleSubmit = (e) => {
    e.preventDefault();
    const value = parseInt(inputValue, 10);
    if (!isNaN(value) && value > 0) {
      setMaxLogs(value);
    }
  };

  return (
    <div className="logs-container">
      <h2>Historial de Logs</h2>
      <form onSubmit={handleSubmit} className="logs-form">
        <label>
          Máximo de logs a mostrar:
          <input
            type="number"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            min="1"
          />
        </label>
        <button type="submit">Actualizar</button>
      </form>
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
