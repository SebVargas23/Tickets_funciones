// src/components/Navbar.js
import React from 'react';
import logo from '../imagenes/Puma-logo-1.png'; // Asegúrate de que la ruta sea correcta


function removeToken() {
  // Check if the token exists in local storage

  if (localStorage.getItem('token')) {
      console.log(localStorage.getItem('token'))
      localStorage.removeItem('token'); // Remove the token
      console.log('Token successfully removed from local storage.');
      window.location.href = '/login';
  } else {
      console.log('No token found in local storage.');
  }
}

function getInitials(nombreCompleto) {
  if (!nombreCompleto) return ""; // Verificar si está vacío
  const nombres = nombreCompleto.split(" ");
  const iniciales = nombres
    .filter((parte) => parte.trim().length > 0) // Eliminar espacios extra
    .map((parte) => parte[0].toUpperCase()); // Tomar la primera letra en mayúsculas
  return iniciales.slice(0, 2).join(""); // Tomar máximo dos iniciales
}

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
      <div className="navbar-avatar">{getInitials(nombreUsuario)}</div>
    </div>
    <button onClick={removeToken} 
    className="navbar-logout-button"
    >Cerrar sesión</button>
  </header>
);

export default Navbar;
