// src/views/Dashboard.tsx
import { useEffect, useContext } from "react";
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
} from "@chakra-ui/react";
import { AuthContext } from "../context/AuthContext";

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
  const { user, loading } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    if (
      !loading &&
      user &&
      (user.role === "Admin" || user.role === "Gerente")
    ) {
      navigate("/admin/dashboard", { replace: true });
    }
  }, [user, loading, navigate]);

  if (loading || (user && (user.role === "Admin" || user.role === "Gerente"))) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="80vh"
      >
        <Spinner size="xl" />
      </Box>
    );
  }

  // Esto solo se renderizará para el rol "Cliente"
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
