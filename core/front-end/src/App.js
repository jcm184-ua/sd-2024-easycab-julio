import React from 'react';
import Mapa from './components/Mapa';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="header">
        <h1>Mapa de Taxis</h1>
      </header>
      <main className="main-container">
        <Mapa />
      </main>
      <footer className="footer">
        <p>&copy; 2024 - Sistema de Taxis</p>
      </footer>
    </div>
  );
}

export default App;
