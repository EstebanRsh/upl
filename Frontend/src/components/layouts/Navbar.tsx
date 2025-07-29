// src/components/layouts/Navbar.tsx
import {
  Box,
  Flex,
  Heading,
  Button,
  Link as ChakraLink,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

type UserInfo = {
  first_name: string;
  role: string;
};

export default function Navbar() {
  const navigate = useNavigate();

  const userString = localStorage.getItem("user");
  const user: UserInfo | null = userString ? JSON.parse(userString) : null;

  const isAdmin = user?.role === "Admin" || user?.role === "Gerente";
  const isClient = user?.role === "Cliente";

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
          {/* --- ENLACES PARA ADMINISTRADORES --- */}
          {isAdmin && (
            <>
              <ChakraLink as={RouterLink} to="/admin/dashboard" mr={4}>
                Dashboard
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/clients" mr={4}>
                Clientes
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/invoices" mr={4}>
                Facturación
              </ChakraLink>
              {/* --- INICIO DE LA CORRECCIÓN CLAVE --- */}
              <ChakraLink as={RouterLink} to="/admin/settings" mr={6}>
                Configuración
              </ChakraLink>
              {/* --- FIN DE LA CORRECCIÓN CLAVE --- */}
            </>
          )}

          {/* --- ENLACES PARA CLIENTES --- */}
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

          {/* --- ENLACES COMUNES --- */}
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
