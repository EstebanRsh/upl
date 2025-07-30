// src/views/admin/InvoiceDetailView.tsx
import { useState, useEffect, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Box, Button, VStack, useToast } from "@chakra-ui/react";
import { AuthContext } from "../../context/AuthContext";
import { InvoiceDetail } from "../../components/admin/invoice/InvoiceDetail";
import { InvoiceAdminOut } from "../../models/Invoice";

function InvoiceDetailView() {
  const { invoiceId } = useParams<{ invoiceId: string }>();
  const [invoice, setInvoice] = useState<InvoiceAdminOut | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const toast = useToast();

  // --- INICIO DE LA CORRECCIÓN ---
  // La función ahora apunta al endpoint de una sola factura
  const fetchInvoice = async () => {
    if (!token || !invoiceId) return;
    const url = `http://localhost:8000/api/admin/invoices/${invoiceId}`; // URL corregida
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "No se pudo cargar la factura.");
      }
      const data = await response.json();
      setInvoice(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };
  // --- FIN DE LA CORRECCIÓN ---

  useEffect(() => {
    fetchInvoice();
  }, [invoiceId, token]);

  const handleUpdateStatus = async (newStatus: string) => {
    if (!token || !invoiceId) return;
    const url = `http://localhost:8000/api/admin/invoices/${invoiceId}/status`;
    try {
      setIsUpdating(true);
      const response = await fetch(url, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "No se pudo actualizar el estado.");
      }
      const updatedInvoice = await response.json();
      setInvoice(updatedInvoice); // Actualizamos el estado con la factura que devuelve la API
      toast({
        title: "Estado actualizado.",
        description: `La factura #${invoiceId} ha sido marcada como '${newStatus}'.`,
        status: "success",
        duration: 5000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <Box
      p={{ base: 4, md: 8 }}
      bg="gray.800"
      color="white"
      minH="calc(100vh - 4rem)"
    >
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        <Button
          onClick={() => navigate("/admin/invoices")}
          alignSelf="flex-start"
          mb={4}
        >
          Volver a la lista
        </Button>
        <InvoiceDetail
          invoice={invoice}
          isLoading={isLoading}
          error={error}
          onUpdateStatus={handleUpdateStatus}
          isUpdating={isUpdating}
        />
      </VStack>
    </Box>
  );
}

export default InvoiceDetailView;
