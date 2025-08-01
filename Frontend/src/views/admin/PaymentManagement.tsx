// src/views/admin/PaymentManagement.tsx
import { useState, useEffect } from "react";
import {
  Box,
  Heading,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  HStack,
  Button,
} from "@chakra-ui/react";
import { useAuth } from "../../context/AuthContext";
import { Pagination } from "../../components/payments/Pagination";
// Importaremos los componentes que crearemos en los siguientes pasos
import { PaymentList } from "../../components/admin/payments/PaymentList";
import { PaymentFilters } from "../../components/admin/payments/PaymentFilters";
// Importaremos la función del servicio que crearemos en el siguiente paso
import { getAllPayments } from "../../services/adminService";
import { useNavigate } from "react-router-dom";
// Definimos el tipo de dato para un Pago, basándonos en el schema del backend
export interface Payment {
  id: number;
  payment_date: string;
  amount: number;
  payment_method: string;
  invoice_id: number;
  user: {
    firstname: string;
    lastname: string;
    dni: string;
  };
}

// Definimos el tipo para los filtros
export interface Filters {
  search: string;
  month: string;
  year: string;
  payment_method: string;
}

function PaymentManagement() {
  const navigate = useNavigate();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState<Filters>({
    search: "",
    month: "",
    year: "",
    payment_method: "",
  });
  const { token } = useAuth();

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    const fetchPayments = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getAllPayments(token, currentPage, filters);
        setPayments(data.items);
        setTotalPages(data.total_pages);
      } catch (err: any) {
        setError(
          err.response?.data?.detail || "No se pudieron cargar los pagos."
        );
        setPayments([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPayments();
  }, [currentPage, filters, token]);

  const handleFilterChange = (newFilters: Partial<Filters>) => {
    setCurrentPage(1);
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const handleResetFilters = () => {
    setCurrentPage(1);
    setFilters({ search: "", month: "", year: "", payment_method: "" });
  };

  const renderContent = () => {
    if (isLoading && payments.length === 0) {
      return (
        <Box display="flex" justifyContent="center" py={10}>
          <Spinner size="xl" />
        </Box>
      );
    }
    if (error) {
      return (
        <Alert status="error" mt={4}>
          <AlertIcon />
          {error}
        </Alert>
      );
    }
    return <PaymentList payments={payments} />;
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
            Historial de Pagos
          </Heading>
          <Button
            colorScheme="teal"
            onClick={() => navigate("/admin/payments/register")}
          >
            Registrar Pago Manual
          </Button>
        </HStack>

        <PaymentFilters
          onFilterChange={handleFilterChange}
          onResetFilters={handleResetFilters}
          initialFilters={filters}
        />

        {renderContent()}

        {totalPages > 1 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
            isLoading={isLoading}
          />
        )}
      </VStack>
    </Box>
  );
}

export default PaymentManagement;
