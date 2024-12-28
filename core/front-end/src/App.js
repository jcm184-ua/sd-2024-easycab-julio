import React from 'react';
import Mapa from './components/Mapa';
import Logs from './components/Logs';
import TablaTaxis from './components/TablaTaxis';
import TablaClientes from './components/TablaClientes'; // Importa el componente de clientes
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="header">
        <h1>Mapa de Taxis</h1>
      </header>
      <main className="main-container">
        <div className="tablas-container">
          <h2>Información General</h2>
          <TablaTaxis /> {/* Tabla de taxis */}
          <TablaClientes /> {/* Tabla de clientes */}
        </div>
        <div className="map-logs-container">
          <Mapa /> {/* Componente de mapa */}
          <Logs /> {/* Componente de logs */}
        </div>

      </main>
      <footer className="footer">
        <p>&copy; 2024 - EASYCAB - Álvaro && Julio</p>
      </footer>
    </div>
  );
}

export default App;
