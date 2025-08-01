// Frontend/src/services/adminService.ts
import axios from 'axios';
import { NewUser } from '../views/admin/ClientAddView';
import { Filters, Payment } from '../views/admin/PaymentManagement'; // Importamos los nuevos tipos

const API_BASE_URL = 'http://localhost:8000/api/admin';

// Esta es la interfaz principal para un usuario, la usaremos en toda la sección de admin
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
  invoices?: Invoice[];
}

export interface Invoice {
  id: number;
  invoice_date: string;
  due_date: string;
  total_amount: number;
  amount: number;
  status: 'Pagado' | 'Pendiente' | 'Pendiente con Comprobante' | 'Vencido' | 'Rechazado';
  receipt_path: string | null;
}

// Interfaz para los datos que se envían al actualizar
interface UpdateData {
    firstname: string;
    lastname: string;
    address: string | null;
    barrio: string | null;
    city: string | null;
    phone: string | null;
    phone2: string | null;
}

// --- Funciones de Gestión de Clientes ---

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
  return response.data.items;
};

export const deleteUser = async (userId: number, token: string): Promise<void> => {
  await axios.delete(`${API_BASE_URL}/users/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
};

export const getUserById = async (userId: number, token: string): Promise<UserDetail> => {
  const response = await axios.get(`${API_BASE_URL}/users/id/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const updateUserDetails = async (userId: number, data: UpdateData, token: string): Promise<any> => {
    const response = await axios.put(`${API_BASE_URL}/users/${userId}/details`, data, {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
};


// --- Funciones de Gestión de Pagos ---

/**
 * Obtiene una lista paginada de todos los pagos para el panel de administrador.
 */
export const getAllPayments = async (token: string, page: number, filters: Filters) => {
  const params = new URLSearchParams({
    page: String(page),
    size: '10',
  });

  if (filters.search) params.append('search', filters.search);
  if (filters.month) params.append('month', filters.month);
  if (filters.year) params.append('year', filters.year);
  if (filters.payment_method) params.append('payment_method', filters.payment_method);

  const response = await axios.get(`http://localhost:8000/api/admin/payments/all`, {
    headers: { Authorization: `Bearer ${token}` },
    params: params,
  });
  
  return response.data as { items: Payment[], total_pages: number };
};

export const getPendingInvoicesByUserId = async (userId: number, token: string): Promise<Invoice[]> => {
  // Nota: Asumimos que el backend tiene un endpoint para esto. Si no, lo crearemos.
  // Por ahora, simularemos este endpoint, pero lo ideal es que exista /api/admin/users/{userId}/pending-invoices
  const response = await axios.get(`http://localhost:8000/api/admin/invoices/all?status=Pendiente&user_id=${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  // El endpoint /invoices/all devuelve un objeto paginado, extraemos los items.
  return response.data.items;
};

export const registerManualPayment = async (formData: FormData, token:string): Promise<any> => {
  const response = await axios.post(`http://localhost:8000/api/admin/payments/register`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data', // Esencial para la subida de archivos
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
};

export const searchUsers = async (query: string, token: string): Promise<UserDetail[]> => {
  // El endpoint es /api/admin/users/search y el parámetro es 'q'
  const response = await axios.get(`http://localhost:8000/api/admin/users/search`, {
    headers: { Authorization: `Bearer ${token}` },
    params: { q: query },
  });
  return response.data;
};