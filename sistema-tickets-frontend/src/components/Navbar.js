// src/components/Navbar.js
import React from 'react';
import logo from '../imagenes/Puma-logo-1.png'; // Asegúrate de que la ruta sea correcta

const Navbar = ({ nombreUsuario }) => (
  <header className="navbar">
    {/* Logo Section */}
    <div className="navbar-logo">
      <img src={logo} alt="Logo" style={{ width: '40px' }} />
    </div>
    
    {/* Search Bar */}
    <input
      type="text"
      placeholder="Alguna búsqueda..."
      className="navbar-search-bar"
    />
    
    {/* User Info Section */}
    <div className="navbar-user-info">
      <span className="navbar-username">{nombreUsuario}</span>
      <div className="navbar-avatar">CP</div>
    </div>
  </header>
);

export default Navbar;
