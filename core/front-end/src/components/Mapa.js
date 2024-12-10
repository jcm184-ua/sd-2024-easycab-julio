import React, { useState, useEffect } from 'react';
import './Mapa.css';

const SIZE = 20; // Tamaño del mapa (cuadrícula)

const Mapa = () => {
  const [mapData, setMapData] = useState({});

  // Función para obtener datos del mapa desde la API
  const fetchMapData = async () => {
    try {
      console.log('Fetching map data...');
      const response = await fetch('http://localhost:5000/estadoActual-mapa');
      const data = await response.json();
      console.log('Datos del mapa:', data);  // Añadir un log para ver los datos
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
    return () => {
      console.log('Clearing interval');
      clearInterval(interval);
    };
  }, []);

  // Función para determinar el color según el tipo
  const getColor = (type) => {
    if (type.startsWith('localizacion')) return 'blue';
    if (type.startsWith('taxi')) return 'green';
    if (type.startsWith('cliente')) return 'yellow';
    return 'gray'; // Color por defecto
  };

  // Generar la cuadrícula
  const renderGrid = () => {
    const grid = [];
    for (let i = 1; i <= SIZE; i++) {
      const row = [];
      for (let j = 1; j <= SIZE; j++) {
        const key = `${i},${j}`; // Coordenada actual de la celda (por ejemplo, "5,3")
        
        // Busca si alguna coordenada del mapa coincide con la clave (como "5,3")
        const cellContent = Object.keys(mapData).find((k) => mapData[k] === key);
        
        // Si encuentra una coincidencia, muestra el nombre de la clave (por ejemplo, "localizacion_A")
        if (cellContent) {
          // Extrae la parte después del guion bajo (_) para obtener la ID
          const id = cellContent.split('_')[1];

          // Determina el color según el tipo
          const color = getColor(cellContent);

          row.push(
            <div
              key={key}
              className="cell"
              style={{ backgroundColor: color, color: 'white' }}
            >
              {id} {/* Muestra solo la ID */}
            </div>
          );
        } else {
          row.push(
            <div key={key} className="cell"></div> // Si no hay contenido, dejar la celda vacía
          );
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
