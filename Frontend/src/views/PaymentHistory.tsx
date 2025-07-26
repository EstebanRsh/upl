// src/views/PaymentHistory.tsx
import { useState, useEffect, useRef } from "react";
import {
  Box,
  Heading,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  useToast,
  HStack,
} from "@chakra-ui/react";
import { InvoiceFilter } from "../components/payments/InvoiceFilter";
import { InvoiceList } from "../components/payments/InvoiceList";
import { Pagination } from "../components/payments/Pagination";

// Se exporta el tipo para que otros componentes como InvoiceList puedan importarlo.
export type Invoice = {
  id: number;
  issue_date: string;
  due_date: string;
  total_amount: number;
  status: "pending" | "paid" | "overdue" | "in_review";
  receipt_pdf_url: string | null;
  user_receipt_url: string | null;
};

function PaymentHistory() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isPaginating, setIsPaginating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({ month: "", year: "" });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(
    null
  );

  // Se define la función fetchInvoices DENTRO del componente para que tenga acceso a los estados.
  const fetchInvoices = async (page: number, month: string, year: string) => {
    const isFirstLoad =
      page === 1 &&
      filters.month === "" &&
      filters.year === "" &&
      invoices.length === 0;
    if (isFirstLoad) {
      setIsInitialLoading(true);
    } else {
      setIsPaginating(true);
    }
    setError(null);

    const token = localStorage.getItem("token");
    let url = `http://localhost:8000/api/users/me/invoices?page=${page}&size=5`;
    if (month) url += `&month=${month}`;
    if (year) url += `&year=${year}`;

    try {
      if (!token) throw new Error("No se encontró token de sesión.");
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || "No se pudieron cargar las facturas."
        );
      }
      const data = await response.json();
      setInvoices(data.items);
      setTotalPages(data.total_pages);
      setCurrentPage(data.current_page);
    } catch (err: any) {
      setError(err.message);
      setInvoices([]);
    } finally {
      setIsInitialLoading(false);
      setIsPaginating(false);
    }
  };

  // useEffect ahora solo se encarga de llamar a fetchInvoices cuando algo cambia.
  useEffect(() => {
    fetchInvoices(currentPage, filters.month, filters.year);
  }, [currentPage, filters]);

  const handleFilterChange = (month: string, year: string) => {
    setCurrentPage(1);
    setFilters({ month, year });
  };

  const handleDownloadReceipt = async (invoiceId: number) => {
    const token = localStorage.getItem("token");
    const DOWNLOAD_URL = `http://localhost:8000/api/invoices/${invoiceId}/download`;
    const toastId = toast({
      title: "Preparando descarga...",
      status: "info",
      duration: null,
      isClosable: true,
    });
    try {
      const response = await fetch(DOWNLOAD_URL, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "No se pudo descargar el recibo.");
      }
      const contentDisposition = response.headers.get("content-disposition");
      let filename = `recibo_${invoiceId}.pdf`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch?.[1]) filename = filenameMatch[1];
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.update(toastId, {
        title: "Descarga iniciada",
        status: "success",
        duration: 3000,
      });
    } catch (err: any) {
      toast.update(toastId, {
        title: "Error de descarga",
        description: err.message,
        status: "error",
        duration: 5000,
      });
    }
  };

  const handleUploadClick = (invoiceId: number) => {
    setSelectedInvoiceId(invoiceId);
    fileInputRef.current?.click();
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file || !selectedInvoiceId) return;
    const UPLOAD_URL = `http://localhost:8000/api/invoices/${selectedInvoiceId}/upload-receipt`;
    const token = localStorage.getItem("token");
    const formData = new FormData();
    formData.append("file", file);
    const toastId = toast({
      title: "Subiendo archivo...",
      status: "info",
      duration: null,
    });
    try {
      const response = await fetch(UPLOAD_URL, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || "Error al subir el archivo.");
      toast.update(toastId, {
        title: "Éxito",
        description: data.message,
        status: "success",
        duration: 5000,
      });
      fetchInvoices(currentPage, filters.month, filters.year);
    } catch (err: any) {
      toast.update(toastId, {
        title: "Error",
        description: err.message,
        status: "error",
        duration: 5000,
      });
    } finally {
      if (event.target) event.target.value = "";
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
        <HStack justify="space-between" wrap="wrap" gap={4}>
          <Heading as="h1" size="xl">
            Mis Facturas
          </Heading>
          <InvoiceFilter onFilterChange={handleFilterChange} />
        </HStack>

        {isInitialLoading ? (
          <Box display="flex" justifyContent="center" py={10}>
            <Spinner size="xl" />
          </Box>
        ) : error ? (
          <Alert status="error" mt={4}>
            <AlertIcon />
            {error}
          </Alert>
        ) : (
          <InvoiceList
            invoices={invoices}
            onUploadClick={handleUploadClick}
            onDownloadClick={handleDownloadReceipt}
            isLoading={isPaginating}
          />
        )}

        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          isLoading={isPaginating}
        />
      </VStack>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept="application/pdf,image/png,image/jpeg"
      />
    </Box>
  );
}

export default PaymentHistory;
