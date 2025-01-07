import React, { useState, useEffect } from 'react';
import './TablaTaxis.css';

const TablaClientes = () => {
  const [clientes, setClientes] = useState([]);

  // Función para obtener datos de la API
  const fetchClientesData = async () => {
    try {
      const response = await fetch('http://localhost:5000/estadoActual-mapa'); // Cambia esta URL según tu API
      const data = await response.json();
      setClientes(data.clientes || []);
    } catch (error) {
      console.error('Error al obtener datos de los clientes:', error);
    }
  };

  // Llamada inicial para cargar los datos
  useEffect(() => {
    fetchClientesData();
    const interval = setInterval(fetchClientesData, 1000); // Actualización cada segundo
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="tabla-taxis-container">
      <h1>Información de Clientes</h1>
      <table className="tabla-taxis">
        <thead>
          <tr>
            <th>ID</th>
            <th>Taxi Asignado</th>
            <th>Destino</th>
          </tr>
        </thead>
        <tbody>
          {clientes.map((cliente) => (
            <tr key={cliente.id}>
              <td>{cliente.id}</td>
              <td>{cliente.taxiAsignado || 'NO TIENE'}</td>
              <td>{cliente.destino || 'NO TIENE'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TablaClientes;
