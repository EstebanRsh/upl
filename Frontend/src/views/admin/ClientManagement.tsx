// src/views/admin/ClientManagement.tsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
import { ClientList } from "../../components/admin/ClientList";
import { ClientSearch } from "../../components/admin/ClientSearch";
import { Pagination } from "../../components/payments/Pagination";
import { getPaginatedUsers, UserDetail } from "../../services/adminService"; // <-- ¡CAMBIO IMPORTANTE!

// Exportamos el tipo para que otros componentes puedan usarlo
export type User = UserDetail;

function ClientManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();
  const { token } = useAuth();

  useEffect(() => {
    // Si no hay token, no hacemos nada.
    if (!token) {
      setIsLoading(false);
      setError("No estás autenticado.");
      return;
    }

    const fetchUsers = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // --- ¡LÓGICA CORREGIDA! Usamos nuestro servicio estandarizado ---
        const data = await getPaginatedUsers(token, currentPage, searchTerm);
        setUsers(data.items);
        setTotalPages(data.total_pages);
      } catch (err: any) {
        console.error("Error al cargar usuarios:", err);
        const errorMessage =
          err.response?.data?.detail || "No se pudieron cargar los usuarios.";
        setError(errorMessage);
        setUsers([]); // Limpiamos los usuarios en caso de error
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, [currentPage, searchTerm, token]);

  const handleSearch = (term: string) => {
    setCurrentPage(1); // Resetea a la primera página en cada nueva búsqueda
    setSearchTerm(term);
  };

  const renderContent = () => {
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
    // Pasamos el tipo de dato correcto a ClientList
    return <ClientList users={users} />;
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
            Gestión de Clientes
          </Heading>
          <HStack>
            <ClientSearch onSearch={handleSearch} />
            <Button
              colorScheme="teal"
              onClick={() => navigate("/admin/clients/add")}
            >
              Añadir Cliente
            </Button>
          </HStack>
        </HStack>

        {renderContent()}

        {totalPages > 1 && !error && (
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

export default ClientManagement;
