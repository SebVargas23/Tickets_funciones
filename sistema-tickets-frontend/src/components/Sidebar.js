// src/components/Sidebar.js
import React from 'react';
import { Link } from 'react-router-dom';


const Sidebar = ({ userRole }) => {
  console.log("rol usuario: ", userRole)
  return (
    <div className="sidebar">
      <ul>
        {/* Opciones comunes para todos los usuarios */}
        <li>
          <Link to="/tickets">Tickets</Link>
        </li>
        <li>
          <Link to="/tickets-list">Lista de Tickets</Link>
        </li>
        <li>
          <Link to="/registro">Usuario</Link>
        </li>
        {/* Opciones exclusivas para el administrador */}
        {userRole === 'admin' && (
          <>
            <li>
              <Link to="/dashboard">Dashboard</Link>
            </li>
            
            <li>
              <Link to="/tickets-cerrados">Tickets Cerrados</Link>
            </li>
            <li>
              <Link to="/sla-data">Datos de sla</Link>
            </li>
          </>
        )}
      </ul>
    </div>
  );
};

export default Sidebar;
