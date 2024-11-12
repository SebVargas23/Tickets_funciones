import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000/',  // La URL base de tu API Django
    headers: {
      //'ngrok-skip-browser-warning': 'any-value',
      'Content-Type': 'application/json',
      },
  });
export default apiClient; 