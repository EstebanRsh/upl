// src/components/layouts/Navbar.tsx
import { useContext } from "react";
import {
  Box,
  Flex,
  Heading,
  Button,
  Link as ChakraLink,
  HStack,
  Text,
  Avatar,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext"; // 1. Importamos el contexto

export default function Navbar() {
  // 2. Consumimos el contexto para obtener el usuario y la función de logout
  const { user, logout } = useContext(AuthContext);

  // 3. La lógica de roles ahora es más simple y segura
  const isAdmin = user?.role === "administrador";
  const isClient = user?.role === "cliente";

  const handleLogout = () => {
    logout(); // Usamos la función del contexto
    // No es necesario llamar a navigate, el guardián de rutas se encargará
  };

  return (
    <Box
      bg="gray.900"
      color="white"
      px={4}
      shadow="md"
      position="sticky"
      top={0}
      zIndex="banner"
    >
      <Flex
        h={16}
        alignItems="center"
        justifyContent="space-between"
        maxW="1200px"
        mx="auto"
      >
        <Heading as="h1" size="md">
          {/* El enlace principal lleva al dashboard correspondiente según el rol */}
          <RouterLink to={isAdmin ? "/admin/dashboard" : "/dashboard"}>
            UPL Pagos
          </RouterLink>
        </Heading>

        <HStack as="nav" spacing={4} display={{ base: "none", md: "flex" }}>
          {/* --- ENLACES PARA ADMINISTRADORES --- */}
          {isAdmin && (
            <>
              <ChakraLink as={RouterLink} to="/admin/dashboard">
                Dashboard
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/clients">
                Clientes
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/invoices">
                Facturación
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/payments">
                Pagos
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/admin/settings">
                Configuración
              </ChakraLink>
            </>
          )}

          {/* --- ENLACES PARA CLIENTES --- */}
          {isClient && (
            <>
              <ChakraLink as={RouterLink} to="/dashboard">
                Mi Resumen
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/payments">
                Mis Pagos
              </ChakraLink>
              <ChakraLink as={RouterLink} to="/services">
                Mis Servicios
              </ChakraLink>
            </>
          )}
        </HStack>

        <HStack spacing={4}>
          {user && (
            <ChakraLink
              as={RouterLink}
              to="/profile"
              display="flex"
              alignItems="center"
            >
              <Avatar size="sm" name={user.first_name} mr={2} />
              <Text fontWeight="bold">{user.first_name}</Text>
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
        </HStack>
      </Flex>
    </Box>
  );
}
