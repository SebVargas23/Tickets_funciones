import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import '../App.css';
import apiClient from '../components/apiClient';

const EditTicket = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState({});
  const [categorias, setCategorias] = useState([]);
  const [prioridades, setPrioridades] = useState([]);
  const [estados, setEstados] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No estás autenticado. Por favor, inicia sesión.');
        navigate('/login');
        return;
      }

      try {
        const [ticketRes, categoriasRes, prioridadesRes, estadosRes] = await Promise.all([
          apiClient.get(`tickets/${id}/`, {
            headers: { 'Authorization': `Bearer ${token}` },
          }),
          apiClient.get('categorias/', {
            headers: { 'Authorization': `Bearer ${token}` },
          }),
          apiClient.get('prioridades/', {
            headers: { 'Authorization': `Bearer ${token}` },
          }),
          apiClient.get('estados/', {
            headers: { 'Authorization': `Bearer ${token}` },
          })
        ]);

        setTicket(ticketRes.data);
        setCategorias(categoriasRes.data);
        setPrioridades(prioridadesRes.data);
        setEstados(estadosRes.data);
      } catch (err) {
        console.error('Error al obtener los datos:', err);
        setError('Hubo un problema al cargar los datos.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setTicket({ ...ticket, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');

    // Ajustar el estado al ID correspondiente
    const estadoSeleccionado = estados.find((estado) => estado.nom_estado === ticket.estado);
    const ticketData = {
      ...ticket,
      estado: estadoSeleccionado ? estadoSeleccionado.id : ticket.estado,
    };

    // Filtrar los campos de solo lectura antes de enviar

    try {
      await apiClient.patch(`tickets/${id}/`, ticketData, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      alert('Ticket actualizado con éxito');
      navigate('/tickets-list');
    } catch (err) {
      console.error('Error al actualizar el ticket:', err);
      setError('Hubo un problema al actualizar el ticket.');
    }
  };

  const handleCloseTicket = async () => {
    const token = localStorage.getItem('token');
    const estadoCerrado = estados.find((estado) => estado.nom_estado === 'Cerrado');
    if (!estadoCerrado) {
      alert('No se encontró el estado "Cerrado".');
      return;
    }

    const ticketData = {
      ...ticket,
      estado: estadoCerrado.id,
      fecha_cierre: new Date().toISOString(),
    };

    delete ticketData.user;
    delete ticketData.fecha_creacion;

    try {
      await apiClient.patch(`tickets/${id}/`, ticketData, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      alert('El ticket ha sido cerrado con éxito');
      navigate('/tickets-list');
    } catch (err) {
      console.error('Error al cerrar el ticket:', err);
      setError('Hubo un problema al cerrar el ticket.');
    }
  };

  const handleReopenTicket = async () => {
    const token = localStorage.getItem('token');
    const estadoEnProceso = estados.find((estado) => estado.nom_estado === 'En proceso');

    if (!estadoEnProceso) {
      setError('No se pudo encontrar el estado "En proceso".');
      return;
    }

    const ticketData = {
      ...ticket,
      estado: estadoEnProceso.id,
      fecha_cierre: null,
    };

    delete ticketData.user;
    delete ticketData.fecha_creacion;

    try {
      await apiClient.patch(`tickets/${id}/`, ticketData, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      alert('El ticket ha sido reabierto con éxito');
      navigate('/tickets-list');
    } catch (err) {
      console.error('Error al reabrir el ticket:', err);
      setError('Hubo un problema al reabrir el ticket.');
    }
  };

  if (loading) return <p>Cargando...</p>;
  if (error) return <p>{error}</p>;

  return (
    <div className="ticket-section-container">
      <h2>🎫 Editar Ticket</h2>

      <div className="ticket-card">
        <div className="ticket-header">
          <div className="ticket-avatar">
            <span className="avatar-placeholder">👤</span>
          </div>
          <div className="ticket-info">
            <h4>Creado por: {ticket.user || 'No disponible'}</h4>
            <span>Fecha de creación: {ticket.fecha_creacion ? new Date(ticket.fecha_creacion).toLocaleDateString() : 'No disponible'}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Título:</label>
            <input
              type="text"
              name="titulo"
              value={ticket.titulo || ''}
              onChange={handleChange}
              required
            />
          </div>

          <div className="input-group">
            <label>Comentario:</label>
            <textarea
              name="comentario"
              value={ticket.comentario || ''}
              onChange={handleChange}
            />
          </div>

          <div className="input-group">
            <label>Categoría:</label>
            <select name="categoria" value={ticket.categoria || ''} onChange={handleChange}>
              <option value="">Seleccione una categoría</option>
              {categorias.map((categoria) => (
                <option key={categoria.id} value={categoria.id}>
                  {categoria.nom_categoria}
                </option>
              ))}
            </select>
          </div>

          <div className="input-group">
            <label>Prioridad:</label>
            <select name="prioridad" value={ticket.prioridad || ''} onChange={handleChange}>
              <option value="">Seleccione una prioridad</option>
              {prioridades.map((prioridad) => (
                <option key={prioridad.id} value={prioridad.id}>
                  {prioridad.num_prioridad}
                </option>
              ))}
            </select>
          </div>

          <div className="input-group">
            <label>Estado:</label>
            <select name="estado" value={ticket.estado || ''} onChange={handleChange}>
              <option value="">Seleccione un estado</option>
              {estados.map((estado) => (
                <option key={estado.id} value={estado.id}>
                  {estado.nom_estado}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" className="update-button">Actualizar</button>
        </form>

        {ticket.estado === 'Cerrado' ? (
          <button onClick={handleReopenTicket} className="reopen-button">Reabrir Ticket</button>
        ) : (
          <button onClick={handleCloseTicket} className="close-button">Cerrar Ticket</button>
        )}

        <button onClick={() => navigate('/tickets-list')} className="back-button">Volver a Lista de Tickets</button>
      </div>
    </div>
  );
};

export default EditTicket;
