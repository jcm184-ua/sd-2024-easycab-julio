const API_URL = 'http://localhost:5000';

export const getMapa = async () => {
  const response = await fetch(`${API_URL}/estado-actual`);
  if (!response.ok) {
    throw new Error('Error al obtener el mapa');
  }
  return response.json();
};
