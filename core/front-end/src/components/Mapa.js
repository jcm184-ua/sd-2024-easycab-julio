import React, { useState, useEffect } from 'react';
import './Mapa.css';

const SIZE = 20; // Tamaño del mapa (cuadrícula)

const Mapa = () => {
  const [mapData, setMapData] = useState({ taxis: [], clientes: [], localizaciones: {} });

  // Función para obtener datos del mapa desde la API
  const fetchMapData = async () => {
    try {
      console.log('Fetching map data...');
      const response = await fetch('http://localhost:5000/estadoActual-mapa');
      const data = await response.json();
      console.log('Datos del mapa:', data);  // Log para depuración
      setMapData(data);
    } catch (error) {
      console.error('Error al obtener datos del mapa:', error);
    }
  };

  // Llamada inicial y actualizaciones periódicas
  useEffect(() => {
    console.log('useEffect called');
    fetchMapData();
    const interval = setInterval(fetchMapData, 1000); // Actualización cada segundo
    return () => clearInterval(interval);
  }, []);

  // Función para determinar el color según el tipo
  const getColor = (type) => {
    switch (type) {
      case 'taxi': return 'green';
      case 'cliente': return 'yellow';
      case 'localizacion': return 'blue';
      default: return 'gray';
    }
  };

  // Función para verificar si una celda tiene contenido y devolver detalles
  const getCellContent = (i, j) => {
    const position = `${i},${j}`;

    // Verifica taxis
    const taxi = mapData.taxis.find((t) => t.posicion === position);
    if (taxi) return { id: `${taxi.id}`, type: 'taxi' };

    // Verifica clientes
    const cliente = mapData.clientes.find((c) => c.posicion === position);
    if (cliente) return { id: `${cliente.id}`, type: 'cliente' };

    // Verifica localizaciones (asegurándonos de que 'localizaciones' y 'locations' existan)
    if (mapData.localizaciones && mapData.localizaciones.locations) {
      const localizacion = mapData.localizaciones.locations.find((loc) => loc.POS === position);
      if (localizacion) return { id: `${localizacion.Id}`, type: 'localizacion' };
    }

    return null; // Celda vacía
  };

  // Generar la cuadrícula
  const renderGrid = () => {
    const grid = [];
    for (let i = 1; i <= SIZE; i++) {
      const row = [];
      for (let j = 1; j <= SIZE; j++) {
        const key = `${i},${j}`; // Coordenada actual de la celda
        const cellContent = getCellContent(i, j);

        if (cellContent) {
          row.push(
            <div
              key={key}
              className="cell"
              style={{ backgroundColor: getColor(cellContent.type), color: 'white' }}
            >
              {cellContent.id}
            </div>
          );
        } else {
          row.push(<div key={key} className="cell"></div>); // Celda vacía
        }
      }
      grid.push(
        <div key={`row-${i}`} className="row">
          {row}
        </div>
      );
    }
    return grid;
  };

  return (
    <div className="map-container">
      <h1>Mapa de Taxis</h1>
      <div className="grid">{renderGrid()}</div>
    </div>
  );
};

export default Mapa;
