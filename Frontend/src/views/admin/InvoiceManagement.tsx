// src/views/admin/InvoiceManagement.tsx
import { useState, useEffect, useContext } from "react";
import {
  Box,
  Heading,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  HStack,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Select,
  Button,
} from "@chakra-ui/react";
import { AuthContext } from "../../context/AuthContext";
import { Pagination } from "../../components/payments/Pagination"; // Reutilizamos la paginación

// Tipos de datos que esperamos del backend
type InvoiceStatus = "pending" | "paid" | "overdue" | "in_review";

type Invoice = {
  id: number;
  issue_date: string;
  due_date: string;
  total_amount: number;
  status: InvoiceStatus;
  user: {
    // Asumimos que el backend puede incluir info básica del usuario
    username: string;
    firstname: string;
    lastname: string;
  };
};

// Componente para el badge de estado
const StatusBadge = ({ status }: { status: InvoiceStatus }) => {
  const statusConfig = {
    paid: { s: "green", t: "Pagada" },
    overdue: { s: "red", t: "Vencida" },
    in_review: { s: "cyan", t: "En Verificación" },
    pending: { s: "yellow", t: "Pendiente" },
  };
  const config = statusConfig[status] || statusConfig.pending;
  return <Badge colorScheme={config.s}>{config.t}</Badge>;
};

function InvoiceManagement() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterStatus, setFilterStatus] = useState<InvoiceStatus | "">("");
  const { token } = useContext(AuthContext);

  useEffect(() => {
    const fetchInvoices = async () => {
      setIsLoading(true);
      // Nota: Necesitarás crear este endpoint en tu backend
      let url = `http://localhost:8000/api/admin/invoices/all?page=${currentPage}&size=10`;
      if (filterStatus) {
        url += `&status=${filterStatus}`;
      }

      try {
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
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    if (token) {
      fetchInvoices();
    }
  }, [currentPage, filterStatus, token]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrentPage(1); // Reinicia a la página 1 al cambiar el filtro
    setFilterStatus(e.target.value as InvoiceStatus | "");
  };

  const renderContent = () => {
    if (isLoading)
      return (
        <Box display="flex" justifyContent="center" py={10}>
          <Spinner size="xl" />
        </Box>
      );
    if (error)
      return (
        <Alert status="error" mt={4}>
          <AlertIcon />
          {error}
        </Alert>
      );
    if (invoices.length === 0)
      return (
        <Box bg="gray.700" p={6} borderRadius="md" textAlign="center">
          <Text color="gray.400">No se encontraron facturas.</Text>
        </Box>
      );

    return (
      <TableContainer bg="gray.700" borderRadius="md">
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th color="white">ID</Th>
              <Th color="white">Cliente</Th>
              <Th color="white">Fecha Emisión</Th>
              <Th color="white">Vencimiento</Th>
              <Th isNumeric color="white">
                Monto
              </Th>
              <Th color="white">Estado</Th>
              <Th color="white">Acciones</Th>
            </Tr>
          </Thead>
          <Tbody>
            {invoices.map((invoice) => (
              <Tr key={invoice.id}>
                <Td>#{invoice.id}</Td>
                <Td>
                  {invoice.user.firstname} {invoice.user.lastname}
                </Td>
                <Td>{new Date(invoice.issue_date).toLocaleDateString()}</Td>
                <Td>{new Date(invoice.due_date).toLocaleDateString()}</Td>
                <Td isNumeric>${invoice.total_amount.toFixed(2)}</Td>
                <Td>
                  <StatusBadge status={invoice.status} />
                </Td>
                <Td>
                  {/* Aquí irían los botones de acción */}
                  <Button size="sm" colorScheme="blue" isDisabled>
                    Ver
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box
      p={{ base: 4, md: 8 }}
      bg="gray.800"
      color="white"
      minH="calc(100vh - 4rem)"
    >
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        <Heading as="h1" size="xl">
          Gestionar Facturas
        </Heading>
        <HStack>
          <Select
            placeholder="Filtrar por estado"
            bg="gray.700"
            onChange={handleFilterChange}
            value={filterStatus}
          >
            <option value="pending">Pendientes</option>
            <option value="paid">Pagadas</option>
            <option value="overdue">Vencidas</option>
            <option value="in_review">En Verificación</option>
          </Select>
        </HStack>
        {renderContent()}
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          isLoading={isLoading}
        />
      </VStack>
    </Box>
  );
}

export default InvoiceManagement;
