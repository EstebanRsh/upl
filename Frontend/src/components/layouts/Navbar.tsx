// src/components/layouts/Navbar.tsx
import {
  Box,
  Flex,
  Heading,
  Button,
  Link as ChakraLink,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <Box bg="gray.800" color="white" px={4} shadow="md">
      <Flex h={16} alignItems="center" justifyContent="space-between">
        <Heading as="h1" size="md">
          <RouterLink to="/dashboard">UPL Pagos</RouterLink>
        </Heading>

        <Flex alignItems="center">
          <ChakraLink as={RouterLink} to="/dashboard" mr={4}>
            Dashboard
          </ChakraLink>
          <ChakraLink as={RouterLink} to="/payments" mr={6}>
            Mis Pagos
          </ChakraLink>
          <Button colorScheme="teal" variant="outline" onClick={handleLogout}>
            Cerrar Sesión
          </Button>
        </Flex>
      </Flex>
    </Box>
  );
}
