import { useState, useEffect } from "react";
import { Link as RouterLink } from "react-router-dom";
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

// Definimos un tipo para la información del usuario que leeremos del backend
type UserInfo = {
  first_name: string;
  last_name: string;
  role: {
    name: "cliente" | "admin"; // Basado en el modelo de UPL
  };
};

// Componente reutilizable para las tarjetas del dashboard
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

  useEffect(() => {
    const fetchUserData = async () => {
      const token = localStorage.getItem("token");
      // Endpoint para obtener los datos del usuario logueado en tu backend UPL
      const USER_ME_URL = "http://localhost:8000/api/users/me";

      try {
        if (!token) {
          throw new Error(
            "No se encontró token de sesión. Por favor, inicie sesión de nuevo."
          );
        }

        const response = await fetch(USER_ME_URL, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "No se pudieron cargar los datos del usuario."
          );
        }

        const data: UserInfo = await response.json();
        setUser(data);
        // Guardamos los datos del usuario en localStorage para poder usarlos en otras partes de la app
        localStorage.setItem("user", JSON.stringify(data));
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, []); // El array vacío asegura que este efecto se ejecute solo una vez

  // --- RENDERIZADO CONDICIONAL ---

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="80vh"
      >
        <Spinner size="xl" color="teal.300" />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={8}>
        <Alert status="error" variant="solid" bg="red.800" borderRadius="md">
          <AlertIcon />
          {error}
        </Alert>
      </Box>
    );
  }

  const isClient = user?.role.name === "cliente";
  const isAdmin = user?.role.name === "admin";

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
        {/* --- TARJETAS PARA CLIENTES --- */}
        {isClient && (
          <>
            <DashboardCard to="/payments" title="Mis Pagos">
              Consulta tu historial de pagos y facturas pendientes.
            </DashboardCard>
            <DashboardCard to="/services" title="Mis Servicios">
              Revisa los detalles de tu plan de internet actual.
            </DashboardCard>
          </>
        )}

        {/* --- TARJETAS PARA ADMINISTRADORES --- */}
        {isAdmin && (
          <>
            <DashboardCard to="/admin/clients" title="Gestionar Clientes">
              Busca, edita o crea nuevos perfiles de clientes.
            </DashboardCard>
            <DashboardCard to="/admin/invoices" title="Gestionar Facturas">
              Genera y administra las facturas de todos los clientes.
            </DashboardCard>
          </>
        )}

        {/* --- TARJETA COMÚN PARA TODOS --- */}
        <DashboardCard to="/profile" title="Mi Perfil">
          Actualiza tu información personal y de contacto.
        </DashboardCard>
      </SimpleGrid>
    </Box>
  );
}

export default Dashboard;
