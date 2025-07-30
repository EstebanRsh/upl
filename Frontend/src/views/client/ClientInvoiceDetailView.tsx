// src/views/ClientInvoiceDetailView.tsx

import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Box, Button, VStack } from "@chakra-ui/react";
import { Invoice } from "../PaymentHistory";
import { InvoiceDetail } from "../../components/admin/invoice/InvoiceDetail";
import { InvoiceAdminOut } from "../../models/Invoice";

function ClientInvoiceDetailView() {
  const { invoiceId } = useParams<{ invoiceId: string }>();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchInvoice = async () => {
      if (!invoiceId) return;
      const token = localStorage.getItem("token");
      const url = `http://localhost:8000/api/users/me/invoices/${invoiceId}`;
      try {
        setIsLoading(true);
        const res = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.detail || "Error al cargar la factura.");
        }
        const data = await res.json();
        setInvoice(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInvoice();
  }, [invoiceId]);

  // Adaptador que transforma un Invoice (cliente) a InvoiceAdminOut (admin)
  const mapToInvoiceAdminOut = (invoice: Invoice): InvoiceAdminOut => ({
    id: invoice.id,
    issue_date: invoice.issue_date,
    due_date: invoice.due_date,
    total_amount: invoice.total_amount,
    base_amount: invoice.total_amount, // ajusta si sabes dividir monto/mora
    late_fee: 0, // ajusta si tienes datos reales
    status: invoice.status,
    receipt_pdf_url: null,
    user_receipt_url: invoice.user_receipt_url,
    user: {
      username: "cliente",
      firstname: "N/A",
      lastname: "N/A",
    },
  });

  return (
    <Box p={{ base: 4, md: 8 }} bg="gray.800" color="white" minH="100vh">
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        <Button onClick={() => navigate("/payments")} alignSelf="flex-start">
          Volver a Mis Facturas
        </Button>
        <InvoiceDetail
          invoice={invoice ? mapToInvoiceAdminOut(invoice) : null}
          isLoading={isLoading}
          error={error}
          onUpdateStatus={() => {}}
          isUpdating={false}
        />
      </VStack>
    </Box>
  );
}

export default ClientInvoiceDetailView;
