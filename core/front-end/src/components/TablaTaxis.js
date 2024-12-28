import React, { useState, useEffect } from 'react';
import './TablaTaxis.css';

const TablaTaxis = () => {
  const [taxis, setTaxis] = useState([]);

  // Función para obtener datos de la API
  const fetchTaxisData = async () => {
    try {
      const response = await fetch('http://localhost:5000/estadoActual-mapa');
      const data = await response.json();
      setTaxis(data.taxis || []);
    } catch (error) {
      console.error('Error al obtener datos de los taxis:', error);
    }
  };

  // Llamada inicial para cargar los datos
  useEffect(() => {
    fetchTaxisData();
    const interval = setInterval(fetchTaxisData, 1000); // Actualización cada segundo
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="tabla-taxis-container">
      <h1>Estado de los Taxis</h1>
      <table className="tabla-taxis">
        <thead>
          <tr>
            <th>ID</th>
            <th>Estado</th>
            <th>Sensores</th>
            <th>Token</th>
            <th>Destino</th>
            <th>Cliente</th>
          </tr>
        </thead>
        <tbody>
          {taxis.map((taxi) => (
            <tr key={taxi.id}>
              <td>{taxi.id}</td>
              <td>{taxi.estado || 'NO TIENE'}</td>
              <td>{taxi.sensores || 'NO TIENE'}</td>
              <td>{taxi.token || 'NO TIENE'}</td>
              <td>{taxi.destino || 'NO TIENE'}</td>
              <td>{taxi.cliente || 'NO TIENE'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TablaTaxis;
