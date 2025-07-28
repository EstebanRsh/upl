// src/views/admin/ClientManagement.tsx
import { useState, useEffect } from "react";
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
import { ClientSearch } from "../../components/admin/ClientSearch";
import { ClientList } from "../../components/admin/ClientList";
import { Pagination } from "../../components/payments/Pagination"; // Reutilizamos la paginación
import { useNavigate } from "react-router-dom";

// El tipo de dato para un usuario, basado en tu modelo UserOut
export type User = {
  username: string;
  email: string;
  dni: number;
  firstname: string;
  lastname: string;
  role: string;
};

function ClientManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUsers = async () => {
      setIsLoading(true);
      const token = localStorage.getItem("token");
      let url = `http://localhost:8000/api/admin/users/all?page=${currentPage}&size=10`;
      if (searchTerm) {
        url += `&username=${searchTerm}`;
      }
      try {
        if (!token) throw new Error("No se encontró token de sesión.");
        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "No se pudieron cargar los clientes."
          );
        }
        const data = await response.json();
        setUsers(data.items);
        setTotalPages(data.total_pages);
        setCurrentPage(data.current_page);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchUsers();
  }, [currentPage, searchTerm]);

  const handleSearch = (term: string) => {
    setCurrentPage(1); // Volver a la página 1 al buscar
    setSearchTerm(term);
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
            Gestionar Clientes
          </Heading>
          <Button
            colorScheme="green"
            onClick={() => navigate("/admin/clients/create")}
          >
            Crear Nuevo Cliente
          </Button>
        </HStack>

        <ClientSearch onSearch={handleSearch} />

        {isLoading ? (
          <Box display="flex" justifyContent="center" py={10}>
            <Spinner size="xl" />
          </Box>
        ) : error ? (
          <Alert status="error" mt={4}>
            <AlertIcon />
            {error}
          </Alert>
        ) : (
          <ClientList users={users} />
        )}

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

export default ClientManagement;
