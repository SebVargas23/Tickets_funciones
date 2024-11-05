// src/pages/Dashboard.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../App.css';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const Dashboard = () => {
    const [stats, setStats] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await axios.get('https://heron-eminent-starling.ngrok-free.app/api/dashboard/stats/', {
                    headers: {'ngrok-skip-browser-warning': 'any-value' },
                  });
                setStats(response.data);
            } catch (err) {
                setError("Error al cargar estadísticas");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return <p>Cargando...</p>;
    if (error) return <p>{error}</p>;

    const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

    const ticketData = [
        { name: "Abiertos", value: stats.tickets_abiertos || 0 },
        { name: "Cerrados", value: stats.tickets_cerrados || 0 },
        { name: "Pendientes", value: stats.tickets_pendientes || 0 },  // Ejemplo adicional
    ];

    // Datos simulados para el gráfico de actividad
    const monthlyData = [
        { name: 'Enero', users: 400, tickets: 240 },
        { name: 'Febrero', users: 300, tickets: 456 },
        { name: 'Marzo', users: 200, tickets: 139 },
        // Agrega más datos según tu API
    ];

    return (
        <div className="dashboard-container">
            <h2>Dashboard</h2>
            <div className="dashboard-stats">
                <div className="stat-card">
                    <h3>Usuarios Totales</h3>
                    <p>{stats.usuarios_totales}</p>
                </div>
                <div className="stat-card">
                    <h3>Tickets Totales</h3>
                    <p>{stats.tickets_totales}</p>
                </div>
                <div className="stat-card">
                    <h3>Tickets Abiertos</h3>
                    <p>{stats.tickets_abiertos}</p>
                </div>
                <div className="stat-card">
                    <h3>Tickets Cerrados</h3>
                    <p>{stats.tickets_cerrados}</p>
                </div>
                <div className="stat-card">
                    <h3>Tickets Pendientes</h3>
                    <p>{stats.tickets_pendientes}</p>
                </div>
                {/* Agrega más tarjetas de estadísticas aquí */}
            </div>

            <div className="chart-container">
                <h3>Distribución de Tickets</h3>
                <PieChart width={400} height={250}>
                    <Pie
                        data={ticketData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        label
                    >
                        {ticketData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                </PieChart>
            </div>

            <div className="chart-container">
                <h3>Actividad Mensual</h3>
                <LineChart
                    width={600}
                    height={300}
                    data={monthlyData}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="users" stroke="#8884d8" activeDot={{ r: 8 }} />
                    <Line type="monotone" dataKey="tickets" stroke="#82ca9d" />
                </LineChart>
            </div>
        </div>
    );
};

export default Dashboard;
