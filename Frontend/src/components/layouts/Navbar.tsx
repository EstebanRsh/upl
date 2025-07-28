// src/components/layouts/Navbar.tsx
import {
  Box,
  Flex,
  Heading,
  Button,
  Link as ChakraLink,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

// --- INICIO DE LA CORRECCIÓN CLAVE ---
type UserInfo = {
  first_name: string;
  role: string; // El rol es un string
};
// --- FIN DE LA CORRECCIÓN CLAVE ---

export default function Navbar() {
  const navigate = useNavigate();

  const userString = localStorage.getItem("user");
  const user: UserInfo | null = userString ? JSON.parse(userString) : null;

  // --- INICIO DE LA CORRECCIÓN CLAVE ---
  // Ahora un admin puede ser 'Admin' o 'Gerente'
  const isAdmin = user?.role === "Admin" || user?.role === "Gerente";
  const isClient = user?.role === "Cliente";
  // --- FIN DE LA CORRECCIÓN CLAVE ---

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <Box bg="gray.900" color="white" px={4} shadow="md">
      <Flex
        h={16}
        alignItems="center"
        justifyContent="space-between"
        maxW="1200px"
        mx="auto"
      >
        <Heading as="h1" size="md">
          <RouterLink to={isAdmin ? "/admin/dashboard" : "/dashboard"}>
            UPL Pagos
          </RouterLink>
        </Heading>
        <Flex alignItems="center">
          {isAdmin && (
            <>
              <ChakraLink as={RouterLink} to="/admin/dashboard" mr={4}>
                Dashboard
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/clients" mr={4}>
                Clientes
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/invoices" mr={6}>
                Facturación
              </ChakraLink>
            </>
          )}
          {isClient && (
            <>
              <ChakraLink as={RouterLink} to="/dashboard" mr={4}>
                Dashboard
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/payments" mr={6}>
                Mis Pagos
              </ChakraLink>
            </>
          )}
          {user && (
            <ChakraLink as={RouterLink} to="/profile" mr={6} fontWeight="bold">
              {user.first_name}
            </ChakraLink>
          )}
          <Button
            colorScheme="teal"
            variant="outline"
            size="sm"
            onClick={handleLogout}
          >
            Cerrar Sesión
          </Button>
        </Flex>
      </Flex>
    </Box>
  );
}
