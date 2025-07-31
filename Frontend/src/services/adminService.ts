// Frontend/src/services/adminService.ts
import axios from 'axios';
import { NewUser } from '../views/admin/ClientAddView';
const API_BASE_URL = 'http://localhost:8000/api/admin';

// 1. CORRECCIÓN: Definimos un tipo de dato completo para el detalle del usuario
// que coincide con lo que manda el backend y lo que necesita la vista de edición.
export interface UserDetail {
  id: number;
  username: string;
  email: string;
  dni: string;
  firstname: string;
  lastname: string;
  address: string | null;
  barrio: string | null;
  city: string | null;
  phone: string | null;
  phone2: string | null;
  invoices?: Invoice[]; // Las facturas son opcionales
}

export interface Invoice {
  id: number;
  invoice_date: string;
  due_date: string;
  amount: number;
  status: 'Pagado' | 'Pendiente' | 'Pendiente con Comprobante' | 'Vencido' | 'Rechazado';
  receipt_path: string | null;
}

// Objeto para los datos que se envían al actualizar
interface UpdateData {
    firstname: string;
    lastname: string;
    address: string | null;
    barrio: string | null;
    city: string | null;
    phone: string | null;
    phone2: string | null;
}

export const addUser = async (userData: NewUser, token: string): Promise<any> => {
  const response = await axios.post(`${API_BASE_URL}/users/add`, userData, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const getUsersWithInvoices = async (token: string): Promise<UserDetail[]> => {
  const response = await axios.get(`${API_BASE_URL}/users/all?size=100`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  // Nota: El backend actualmente no envía las facturas en esta ruta.
  // El campo 'invoices' estará vacío hasta que se modifique el backend.
  return response.data.items;
};

export const deleteUser = async (userId: number, token: string): Promise<void> => {
  await axios.delete(`http://localhost:8000/api/admin/users/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
};

export const getUserByDni = async (dni: string, token: string): Promise<UserDetail> => {
    const response = await axios.get(`${API_BASE_URL}/users/${dni}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
};

// 2. CORRECCIÓN: Añadimos la función que faltaba para actualizar los datos.
export const updateUserDetails = async (userId: number, data: UpdateData, token: string): Promise<any> => {
    const response = await axios.put(`${API_BASE_URL}/users/${userId}/details`, data, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
};

export const updateInvoiceStatus = async (invoiceId: number, status: 'Pagado' | 'Rechazado', token: string): Promise<any> => {
    const response = await axios.put(`${API_BASE_URL}/invoices/${invoiceId}/status`, 
    { status }, 
    {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
}
export const getUserById = async (userId: number, token: string): Promise<UserDetail> => {
  const response = await axios.get(`${API_BASE_URL}/users/id/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};