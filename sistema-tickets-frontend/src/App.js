// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import './App.css';
import RegistroUsuario from './pages/RegistroUsuario';
import Login from './pages/Login';
import Tickets from './pages/Tickets';
import TicketsList from './pages/TicketsList';
import EditTicket from './pages/EditTicket';
import ClosedTicketsList from './pages/ClosedTicketsList';
import Dashboard from './pages/Dashboard';
import PrivateRoute from './components/PrivateRoute';
import { decodeToken } from './utils';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import apiClient from './components/apiClient';

// Configuración de Axios
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("Error de Axios:", error.message);
    if (error.response && error.response.status === 401) {
      alert('Tu sesión ha expirado. Por favor, inicia sesión de nuevo.');
      localStorage.removeItem('token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

function App() {
  const [nombreUsuario, setNombreUsuario] = useState('');
  const [userRole, setUserRole] = useState('');
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const decodedToken = decodeToken(token);
      if (decodedToken) {
        setNombreUsuario(decodedToken.nom_usuario);
        console.log(decodedToken.nom_usuario);
        setUserRole(decodedToken.role);
        console.log(decodedToken.role);// Guardar el rol del usuario
      }
    }
  }, []);
  console.log(userRole)

  return (
    <Router>
      
      <MainContent nombreUsuario={nombreUsuario} userRole={userRole} />
    </Router>
  );
}

function MainContent({ nombreUsuario, userRole }) {
  const location = useLocation();
  const isLoginRoute = location.pathname === '/login';

  return (
    <div className="app-container">
      {!isLoginRoute && <Header nombreUsuario={nombreUsuario} />}
      {!isLoginRoute && <Sidebar userRole={userRole} />}

      <div className={`main-content ${!isLoginRoute ? 'with-sidebar' : ''}`}>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<PrivateRoute requiredRole="admin"><RegistroUsuario /></PrivateRoute>} />
          <Route path="/dashboard" element={<PrivateRoute requiredRole="admin"><Dashboard /></PrivateRoute>} />
          <Route path="/tickets" element={<PrivateRoute><Tickets /></PrivateRoute>} />
          <Route path="/tickets-list" element={<PrivateRoute><TicketsList /></PrivateRoute>} />
          <Route path="/tickets/edit/:id" element={<PrivateRoute requiredRole="admin"><EditTicket /></PrivateRoute>} />
          <Route path="/tickets-cerrados" element={<PrivateRoute requiredRole="admin"><ClosedTicketsList /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
