// src/views/admin/AdminDashboard.tsx
import { useState, useEffect } from "react";
import {
  Box,
  Heading,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  Icon,
  Text,
} from "@chakra-ui/react";
import {
  FaUsers,
  FaFileInvoiceDollar,
  FaDollarSign,
  FaUserPlus,
} from "react-icons/fa";

// --- Tipos de Datos para las Estadísticas ---
interface ClientStatusSummary {
  active_clients: number;
  suspended_clients: number;
  total_clients: number;
}
interface InvoiceStatusSummary {
  pending: number;
  paid: number;
  overdue: number;
  total: number;
}
interface DashboardStats {
  client_summary: ClientStatusSummary;
  invoice_summary: InvoiceStatusSummary;
  monthly_revenue: number;
  new_subscriptions_this_month: number;
}

// --- Sub-componente para cada Tarjeta de Estadística ---
const StatCard = ({
  icon,
  label,
  value,
  helpText,
  arrowType,
}: {
  icon: any;
  label: string;
  value: string | number;
  helpText?: string;
  arrowType?: "increase" | "decrease";
}) => (
  <Stat
    bg="gray.700"
    p={5}
    borderRadius="lg"
    display="flex"
    alignItems="center"
  >
    <Icon as={icon} boxSize={10} color="teal.300" mr={5} />
    <Box>
      <StatLabel color="gray.400">{label}</StatLabel>
      <StatNumber fontSize="2xl">{value}</StatNumber>
      {helpText && (
        <StatHelpText>
          {arrowType && <StatArrow type={arrowType} />}
          {helpText}
        </StatHelpText>
      )}
    </Box>
  </Stat>
);

function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      const token = localStorage.getItem("token");
      const DASHBOARD_URL = "http://localhost:8000/api/admin/dashboard";
      try {
        if (!token) throw new Error("No se encontró token de sesión.");
        const response = await fetch(DASHBOARD_URL, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "No se pudieron cargar las estadísticas."
          );
        }
        const data = await response.json();
        setStats(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (isLoading) {
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

  return (
    <Box
      p={{ base: 4, md: 8 }}
      bg="gray.800"
      color="white"
      minH="calc(100vh - 4rem)"
    >
      <VStack spacing={8} align="stretch" maxW="1200px" mx="auto">
        <Heading as="h1" size="xl">
          Panel de Administrador
        </Heading>

        {stats && (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
            <StatCard
              icon={FaUsers}
              label="Clientes Activos"
              value={`${stats.client_summary.active_clients} / ${stats.client_summary.total_clients}`}
              helpText={`${stats.client_summary.suspended_clients} suspendidos`}
            />
            <StatCard
              icon={FaFileInvoiceDollar}
              label="Facturas Pendientes"
              value={
                stats.invoice_summary.pending + stats.invoice_summary.overdue
              }
              helpText={`${stats.invoice_summary.overdue} vencidas`}
            />
            <StatCard
              icon={FaDollarSign}
              label="Ingresos del Mes"
              value={`$${stats.monthly_revenue.toLocaleString("es-AR")}`}
              helpText={`${stats.invoice_summary.paid} facturas pagadas`}
            />
            <StatCard
              icon={FaUserPlus}
              label="Nuevos Clientes (Mes)"
              value={stats.new_subscriptions_this_month}
              arrowType="increase"
            />
          </SimpleGrid>
        )}

        {/* Aquí irán los enlaces a las demás secciones de admin */}
        <Box>
          <Heading size="lg" mt={8}>
            Próximos Pasos
          </Heading>
          <Text color="gray.400">
            Desde aquí podrás acceder a las secciones para gestionar clientes,
            facturas, planes y más.
          </Text>
        </Box>
      </VStack>
    </Box>
  );
}

export default AdminDashboard;
