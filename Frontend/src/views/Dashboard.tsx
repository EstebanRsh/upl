// src/views/Dashboard.tsx
import { useState, useEffect } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  Box,
  Heading,
  Text,
  VStack,
  SimpleGrid,
  Card,
  CardHeader,
  CardBody,
  Link,
  Spinner,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";

// --- INICIO DE LA CORRECCIÓN CLAVE ---
type UserInfo = {
  first_name: string;
  role: string; // El rol ahora es un string simple
};
// --- FIN DE LA CORRECCIÓN CLAVE ---

const DashboardCard = ({
  to,
  title,
  children,
}: {
  to: string;
  title: string;
  children: React.ReactNode;
}) => (
  <Link as={RouterLink} to={to} _hover={{ textDecoration: "none" }}>
    <Card
      as="div"
      bg="gray.700"
      color="white"
      _hover={{ transform: "translateY(-5px)", shadow: "lg" }}
      transition="transform 0.2s, box-shadow 0.2s"
      height="100%"
    >
      <CardHeader>
        <Heading size="md">{title}</Heading>
      </CardHeader>
      <CardBody>
        <Text>{children}</Text>
      </CardBody>
    </Card>
  </Link>
);

function Dashboard() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserData = async () => {
      const token = localStorage.getItem("token");
      const USER_ME_URL = "http://localhost:8000/api/users/me";
      try {
        if (!token) throw new Error("No se encontró token de sesión.");
        const response = await fetch(USER_ME_URL, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "No se pudieron cargar los datos."
          );
        }
        const data: UserInfo = await response.json();

        // --- INICIO DE LA CORRECCIÓN CLAVE ---
        // Comprobamos si el rol es Admin o Gerente
        if (data.role === "Admin" || data.role === "Gerente") {
          localStorage.setItem("user", JSON.stringify(data)); // Guardamos los datos antes de redirigir
          navigate("/admin/dashboard", { replace: true });
          return;
        }
        // --- FIN DE LA CORRECCIÓN CLAVE ---

        setUser(data);
        localStorage.setItem("user", JSON.stringify(data));
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchUserData();
  }, [navigate]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <Spinner size="xl" />
      </Box>
    );
  }
  if (error) {
    return (
      <Box p={8}>
        <Alert status="error">
          <AlertIcon />
          {error}
        </Alert>
      </Box>
    );
  }

  // Este JSX solo será visible para los clientes.
  return (
    <Box p={8} bg="gray.800" color="white" minH="calc(100vh - 4rem)">
      <VStack spacing={4} align="stretch" mb={10}>
        <Heading as="h1" size="xl" color="teal.300">
          Bienvenido, {user?.first_name || "Usuario"}
        </Heading>
        <Text fontSize="lg" color="gray.400">
          Gestiona tus servicios y pagos de forma rápida y sencilla.
        </Text>
      </VStack>
      <Heading as="h2" size="lg" mb={6}>
        Accesos Rápidos
      </Heading>
      <SimpleGrid columns={{ sm: 1, md: 2, lg: 3 }} spacing={6}>
        <DashboardCard to="/payments" title="Mis Pagos">
          Consulta tu historial de pagos y facturas pendientes.
        </DashboardCard>
        <DashboardCard to="/services" title="Mis Servicios">
          Revisa los detalles de tu plan de internet actual.
        </DashboardCard>
        <DashboardCard to="/profile" title="Mi Perfil">
          Actualiza tu información personal y de contacto.
        </DashboardCard>
      </SimpleGrid>
    </Box>
  );
}

export default Dashboard;
