import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../components/apiClient';
import '../styles/sla_data.css'

const SlaRelatedData = () => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);  // Added error state
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      // Fetch data from the backend API
      const token = localStorage.getItem('token');
      if (!token) {
        setError('No estás autenticado. Por favor, inicia sesión.');
        navigate('/login');
        return;
      }
      
      try {
        const response = await apiClient.get('sla-presupuestos/', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        setData(response.data);
      } catch (error) {
        console.error("Error fetching data:", error);
        setError('Error al cargar los datos.');
      }
    };

    fetchData();  // Call the fetchData function inside useEffect
  }, [navigate]);

  const calcHoras = (calcMonto) => {
    return ((calcMonto - 1.00) / 0.05).toFixed(2);
  };
  const calcMonto_final = (monto, calcMonto) => {
    return (monto * calcMonto).toFixed(2);
  };

  const handleTicketClick = (ticketId) => {
    // Redirect to the edit ticket page
    navigate(`/edit_ticket/${ticketId}`);
  };

  if (error) {
    return <div>{error}</div>;  // Display error message if there's an error
  }

  if (!data) {
    return <div>Loading...</div>;
  }


  return (
    <div className="sla-related-data">
      <section className="budget-overview">
        <h1>Resumen del presupuesto de este mes</h1>
        <div className="budget-details">
          <p><strong>Presupuesto Mensual:</strong> ${data.presupuesto.presupuesto_mensual}</p>
          <p><strong>Presupuesto Gastado:</strong> ${data.presupuesto.presupuesto_gastado}</p>
          <p><strong>Fecha del Presupuesto:</strong> {data.presupuesto.fecha_presupuesto}</p>
          <p><strong>Presupuesto Restante:</strong> ${data.presupuesto.presupuesto_restante}</p>
          <p><strong>Over Budget:</strong> {data.presupuesto.over_budget ? "Yes" : "No"}</p>
        </div>
      </section>

      <section className="worst-tickets">
        <h2>Casos criticos abiertos</h2>
        <table className="tickets-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Titulo Ticket</th>
              <th>Status SLA</th>
              <th>Costo de Ticket original</th>
              <th>fecha de Cierre Esperado</th>
              <th>Horas de atrazo</th>
              <th>Costo Estimado Del ticket</th>
            </tr>
          </thead>
          <tbody>
            {data.worst_tickets.map((ticket) => (
              <tr key={ticket.ticket_id} onClick={() => handleTicketClick(ticket.ticket_id)} style={{ cursor: 'pointer' }}>
                <td>{ticket.ticket_id}</td>
                <td>{ticket.title}</td>
                <td>{ticket.sla_status}</td>
                <td>${ticket.monto}</td>
                <td>{ticket.dates.find(date => date.type === 'cierre_esperado')?.date}</td>
                <td>{calcHoras(ticket.calculo_monto)}</td>
                <td>${calcMonto_final(ticket.monto, ticket.calculo_monto)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};
export default SlaRelatedData;