import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link, useNavigate } from 'react-router-dom';
import '../App.css';
import { decodeToken } from '../utils';
import Avatar from '../imagenes/Avatar.jpg';

const RegistroUsuario = () => {
    const [formData, setFormData] = useState({
        rut_usuario: '',
        dv_rut_usuario: '',
        nom_usuario: '',
        correo: '',
        telefono: '',
        cargo: '',
        role: 'usuario', // Asume rol 'usuario' por defecto
        password: '',
        password_confirm: ''
    });;

    const [cargos, setCargos] = useState([]);
    const [errors, setErrors] = useState({});
    const navigate = useNavigate();
    const [isAdmin, setIsAdmin] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            const decoded = decodeToken(token);
            setIsAdmin(decoded.role === 'admin');  // Verifica si el usuario actual es admin
        }

        const fetchCargos = async () => {
            try {
                const response = await axios.get('http://127.0.0.1:8000/cargos/');
                setCargos(response.data);
            } catch (error) {
                console.error('Error al obtener los cargos:', error);
            }
        };

        fetchCargos();
    }, []);
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prevData) => ({
            ...prevData,
            [name]: value,
        }));
        setErrors((prevErrors) => ({
            ...prevErrors,
            [name]: undefined,
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Remueve el rol si no es administrador
        const formDataToSend = isAdmin ? formData : { ...formData, role: 'usuario' };

        try {
            const response = await axios.post('http://127.0.0.1:8000/registrar/', formDataToSend);
            console.log('Usuario registrado:', response.data);
            navigate('/login');
        } catch (err) {
            console.error('Error en el registro:', err.response?.data || err.message);
            setErrors(err.response?.data || { error: 'Error desconocido en el registro' });
        }
    };

    return (
        <div className="registration-container">
            <div className="user-profile-section">
            <img src={Avatar} alt="Avatar" className="user-avatar" />
                <h2>{formData.nom_usuario || "Nuevo Usuario"}</h2>
                <p>{formData.cargo ? cargos.find(c => c.id === Number(formData.cargo))?.nom_cargo : "Seleccione un cargo"}</p>
                <button className="follow-button">Seguir</button>
                <p className="description">
                    Bienvenido a la plataforma. Completa los detalles de tu cuenta para continuar.
                </p>
            </div>

            <div className="account-details-section">
                <h3>Detalles de la Cuenta</h3>
                <form onSubmit={handleSubmit}>
                    <div className="form-grid">
                        <div className="input-group">
                            <label>RUT Usuario</label>
                            <input type="text" name="rut_usuario" value={formData.rut_usuario} onChange={handleChange} required />
                            {errors.rut_usuario && <span className="error">{errors.rut_usuario}</span>}
                        </div>

                        <div className="input-group">
                            <label>DV RUT</label>
                            <input type="text" name="dv_rut_usuario" value={formData.dv_rut_usuario} onChange={handleChange} required />
                            {errors.dv_rut_usuario && <span className="error">{errors.dv_rut_usuario}</span>}
                        </div>

                        <div className="input-group">
                            <label>Nombre</label>
                            <input type="text" name="nom_usuario" value={formData.nom_usuario} onChange={handleChange} required />
                            {errors.nom_usuario && <span className="error">{errors.nom_usuario}</span>}
                        </div>

                        <div className="input-group">
                            <label>Correo</label>
                            <input type="email" name="correo" value={formData.correo} onChange={handleChange} required />
                            {errors.correo && <span className="error">{errors.correo}</span>}
                        </div>

                        <div className="input-group">
                            <label>Teléfono</label>
                            <input type="tel" name="telefono" value={formData.telefono} onChange={handleChange} required />
                            {errors.telefono && <span className="error">{errors.telefono}</span>}
                        </div>

                        <div className="input-group">
                            <label>Cargo</label>
                            <select name="cargo" onChange={handleChange} value={formData.cargo} required>
                                <option value="">Seleccione un cargo</option>
                                {cargos.map(cargo => (
                                    <option key={cargo.id} value={cargo.id}>{cargo.nom_cargo}</option>
                                ))}
                            </select>
                            {errors.cargo && <span className="error">{errors.cargo}</span>}
                        </div>

                        {/* Selector de Rol (visible solo para admin) */}
                        {isAdmin && (
                            <div className="input-group">
                                <label>Rol</label>
                                <select name="role" onChange={handleChange} value={formData.role}>
                                    <option value="usuario">Usuario</option>
                                    <option value="admin">Administrador</option>
                                </select>
                                {errors.role && <span className="error">{errors.role}</span>}
                            </div>
                        )}

                        <div className="input-group">
                            <label>Contraseña</label>
                            <input type="password" name="password" value={formData.password} onChange={handleChange} required />
                            {errors.password && <span className="error">{errors.password}</span>}
                        </div>

                        <div className="input-group">
                            <label>Confirmar Contraseña</label>
                            <input type="password" name="password_confirm" value={formData.password_confirm} onChange={handleChange} required />
                            {errors.password_confirm && <span className="error">{errors.password_confirm}</span>}
                        </div>
                    </div>
                    <button type="submit" className="update-account-button">Registrar Usuario</button>
                </form>
                <p>¿Ya tienes una cuenta? <Link to="/login">Inicia sesión aquí</Link></p>
            </div>
        </div>
    );
};

export default RegistroUsuario;
