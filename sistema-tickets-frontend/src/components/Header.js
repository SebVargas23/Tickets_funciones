// src/components/Header.js
import React from 'react';
import logo from '../imagenes/Puma-logo-1.png'; // Ajusta el logo

const Header = ({ nombreUsuario }) => (
  <header className="header">
    <div className="logo">
      <img src={logo} alt="Logo" style={{ width: '40px' }} />
    </div>
    <input type="text" placeholder="Search for something..." className="search-bar" />
    <div className="user-info">
      <span>{nombreUsuario}</span>
      <div className="avatar">CP</div>
    </div>
  </header>
);

export default Header;