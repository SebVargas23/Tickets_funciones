import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Modal from 'react-modal'; // Modal para el formulario
import '../App.css';
import guias from '../json_test/guias.json';

// Configura el estilo del modal
Modal.setAppElement('#root');

const Tickets = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    titulo: '',
    comentario: '',
    categoria: '',
    prioridad: '',
    servicio: '',
    estado: '', // Inicialmente vacío, se llenará al cargar los estados
  });// captura los datos del formulario para posterior post request
  

  const [categorias, setCategorias] = useState([]);
  const [prioridades, setPrioridades] = useState([]);
  const [servicios, setServicios] = useState([]);
  const [estados, setEstados] = useState([]);
  
  const [modalIsOpen, setModalIsOpen] = useState(false); // Estado para el modal
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [guiaContenido, setGuiaContenido] = useState(null);

  const handleGuiaChange = (e) => {
    const categoriaId = parseInt(e.target.value);
    console.log(categoriaId)
    setSelectedCategoryId(categoriaId);

    if (categoriaId === '') {
      setGuiaContenido(null); // Si no hay categoría, no hay contenido
    } else {
      // Aquí busca el contenido de la guía basado en el id de la categoría
      const guia = guias.find(guia => guia.id_categoria === Number(categoriaId));
      setGuiaContenido(guia || null);

      const relatedService = servicios.find(
        (servicio) => servicio.categoria_id === categoriaId
      );

      setFormData((prevData) => ({
        ...prevData,
        categoria: categoriaId, // Establece la categoría en formData
        servicio: relatedService ? relatedService.id : '',
      }));
    }
  }; // maneja cambios en el la guia
  const handleOpenModal = () => {
    setModalIsOpen(true);
  }; // maneja el abrir el modal

  const handleCloseModal = () => {
    setModalIsOpen(false);
    setFormData((prevData) => ({
      ...prevData,
      titulo: '',
      comentario: '',
      prioridad: '',
    }));
  }; // manjea el cerrar el modal

  useEffect(() => {
    const fetchData = async (url, setState) => {
      const token = localStorage.getItem('token');
      if (!token) {
        alert('No estás autenticado. Por favor, inicia sesión.');
        navigate('/login');
        return;
      }

      try {
        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        const data = await response.json();
        setState(data);
        console.log('data: ', data)
      } catch (error) {
        console.error(`Error al cargar los datos desde ${url}:`, error);
      }
    };

    // Cargar todas las listas de datos
    fetchData('http://localhost:8000/categorias/', setCategorias);
    fetchData('http://localhost:8000/prioridades/', setPrioridades);
    fetchData('http://localhost:8000/servicios/', setServicios);
    fetchData('http://localhost:8000/estados/', setEstados);
  }, [navigate]); // gets the data

  useEffect(() => {
    const estadoAbierto = estados.find((estado) => estado.nom_estado === 'Abierto');
    if (estadoAbierto) {
      setFormData((prevData) => ({
        ...prevData,
        estado: estadoAbierto.id,
      }));
    }
  }, [estados]);// Establecer el estado predeterminado como "Abierto" si existe en la lista de estados


  

  const handleCategoryChange = (e) => {
    const categoriaId = parseInt(e.target.value);
    setFormData((prevData) => ({
      ...prevData,
      categoria: categoriaId,
    }));

    const relatedService = servicios.find(
      (servicio) => servicio.categoria_id === categoriaId
    );

    setFormData((prevData) => ({
      ...prevData,
      servicio: relatedService ? relatedService.id : '',
    }));
  }; // manejo de cambios de categoria

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  }; //manejo de cambios generales

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const adjustedData = {
      ...formData,
    };

    const token = localStorage.getItem('token');
    if (!token) {
      alert('No estás autenticado. Por favor, inicia sesión.');
      navigate('/login');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/tickets/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(adjustedData),
      });

      if (response.ok) {
        alert('Ticket creado con éxito');
        navigate('/tickets');
        setFormData({
          titulo: '',
          comentario: '',
          categoria: '',
          prioridad: '',
          servicio: '',
          estado: estados.find((estado) => estado.nom_estado === 'Abierto')?.id || '', // Restablecer a "Abierto"
        });
      } else {
        const errorData = await response.json();
        console.error('Error en la respuesta:', errorData);
        alert(`Error al crear el ticket: ${JSON.stringify(errorData)}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Hubo un problema al crear el ticket');
    }
  }; // manda request post con datos importantes
  return (
    <div className="guia-usuario-container">
      <h2 className="guia-usuario-titulo">Creación de tickets</h2>

      <div className="lista-desplegable">
        <label>Selecciona una categoría:</label>
        <select onChange={handleGuiaChange} value={selectedCategoryId}>
          <option value="">Información general</option>
          {categorias.map((categoria) => (
            <option key={categoria.id} value={categoria.id}>
              {categoria.nom_categoria}
            </option>
          ))}
        </select>
      </div>

      {/* Renderiza información general si no hay categoría seleccionada */}
      {selectedCategoryId === '' ? (
        <p>infro general</p>
      ) : (
        // Renderiza las instrucciones de la guía seleccionada
        guiaContenido && (
          <div className="guia-contenido">
            <h3>{guiaContenido.titulo}</h3>
            <ul>
              {guiaContenido.instrucciones.map((instruccion, index) => (
                <li key={index}>{instruccion}</li>
              ))}
            </ul>
          </div>
        )
      )}

      <button onClick={handleOpenModal} className="open-modal-button">
        🎫 Crear Ticket
      </button>

      {/* Modal para el formulario de creación de ticket */}
      <Modal
        isOpen={modalIsOpen}
        onRequestClose={handleCloseModal}
        contentLabel="Crear Ticket"
        className="custom-modal"
        overlayClassName="modal-overlay"
      >
        <h2>Crear Ticket</h2>

      <form className="ticket-form" onSubmit={handleSubmit}>
          {/* Campos del formulario */}

          {/* Titulo */}
        <div className="input-group">
          <label>📝 Título</label>
          <input
            type="text"
            name="titulo"
            value={formData.titulo}
            onChange={handleChange}
            required
            placeholder="Escribe el título del ticket"
          />
        </div>

        {/* Comentario */}
        <div className="input-group">
          <label>💬 Comentario</label>
          <textarea
            name="comentario"
            value={formData.comentario}
            onChange={handleChange}
            required
            placeholder="Escribe un comentario"
          ></textarea>
        </div>

        {/* Categoría */}
        <div className="input-group">
          <label>📂 Categoría</label>
          <select
            name="categoria"
            value={formData.categoria}
            onChange={handleCategoryChange}
            required
          >
            <option value="">Seleccione una categoría</option>
            {categorias.map((categoria) => (
              <option key={categoria.id} value={categoria.id}>
                {categoria.nom_categoria}
              </option>
            ))}
          </select>
        </div>

        {/* Prioridad */}
        <div className="input-group">
          <label>⚡ Prioridad</label>
          <select
            name="prioridad"
            value={formData.prioridad}
            onChange={handleChange}
            required
          >
            <option value="">Seleccione una prioridad</option>
            {prioridades.map((prioridad) => (
              <option key={prioridad.id} value={prioridad.id}>
                {prioridad.num_prioridad}
              </option>
            ))}
          </select>
        </div>

        {/* Servicio */}
        <div className="input-group">
          <label>🔧 Servicio</label>
          <select
            name="servicio"
            value={formData.servicio}
            required
            disabled
          >
            <option value="">Seleccione un servicio</option>
            {servicios.map((servicio) => (
              <option key={servicio.id} value={servicio.id}>
                {servicio.titulo_servicio}
              </option>
            ))}
          </select>
        </div>

        {/* Estado */}
        <div className="input-group">
          <label>📌 Estado</label>
          <select
            name="estado"
            value={formData.estado}
            onChange={handleChange}
            required
            disabled
          >
            {estados.map((estado) => (
              <option key={estado.id} value={estado.id}>
                {estado.nom_estado}
              </option>
            ))}
          </select>
        </div>

        <button type="submit">🚀 Crear Ticket</button>
      </form>

        {/*<button onClick={handleCloseModal}>Cerrar</button>*/}
      <Link to="/tickets-list" className="view-tickets-link">
        📋 Ver Lista de Tickets
      </Link>
      </Modal>
    </div>
  );
};

export default Tickets;
