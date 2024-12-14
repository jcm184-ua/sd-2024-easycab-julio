import React from 'react';
import Mapa from './components/Mapa';
import Logs from './components/Logs'; // Importamos el nuevo componente
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="header">
        <h1>Mapa de Taxis</h1>
      </header>
      <main className="main-container">
      <div className="map-logs-container">
          <Mapa /> {/* Componente de mapa */}
          <Logs /> {/* Componente de logs */}
        </div>
      </main>
      <footer className="footer">
        <p>&copy; 2024 - Sistema de Taxis</p>
      </footer>
    </div>
  );
}

export default App;
