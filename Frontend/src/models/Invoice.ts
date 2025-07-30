// src/models/Invoice.ts

// Interfaz para la información básica del usuario anidada en la factura
export interface UserBasicInfo {
  username: string;
  firstname: string;
  lastname: string;
}

// Interfaz completa para la factura que se usa en el panel de administrador
export interface InvoiceAdminOut {
  id: number;
  issue_date: string;
  due_date: string;
  base_amount: number;
  late_fee: number;
  total_amount: number;
  status: "pending" | "paid" | "overdue" | "in_review";
  receipt_pdf_url: string | null;
  user_receipt_url: string | null; 
  user: UserBasicInfo;
}