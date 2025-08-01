// src/services/planService.ts
import axios from 'axios';
import { Plan } from '../views/admin/PlanManagement';

// La URL base para los endpoints públicos de planes
const API_PUBLIC_URL = 'http://localhost:8000/api/plans';
// La URL base para los endpoints de administración de planes
const API_ADMIN_URL = 'http://localhost:8000/api/admin/plans';

// Definimos un tipo para los datos que se envían al crear/actualizar un plan
type PlanData = {
  name: string;
  speed_mbps: number;
  price: number;
};

/**
 * Obtiene todos los planes de internet disponibles (endpoint público).
 */
export const getAllPlans = async () => {
  const response = await axios.get(`${API_PUBLIC_URL}/all`);
  // La respuesta es un objeto paginado, lo devolvemos tal cual
  return response.data as { items: Plan[] };
};

/**
 * Crea un nuevo plan de internet (requiere token de admin).
 */
export const createPlan = async (planData: PlanData, token: string) => {
  const response = await axios.post(`${API_ADMIN_URL}/add`, planData, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

/**
 * Actualiza un plan de internet existente por su ID (requiere token de admin).
 */
export const updatePlan = async (planId: number, planData: PlanData, token: string) => {
  const response = await axios.put(`${API_ADMIN_URL}/update/${planId}`, planData, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

/**
 * Elimina un plan de internet por su ID (requiere token de admin).
 */
export const deletePlan = async (planId: number, token: string) => {
  const response = await axios.delete(`${API_ADMIN_URL}/delete/${planId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};