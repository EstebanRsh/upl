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
import { useAuth } from "../../context/AuthContext"; // La importación es correcta
import { ClientList } from "../../components/admin/ClientList";
import { ClientSearch } from "../../components/admin/ClientSearch";
import { Pagination } from "../../components/payments/Pagination";

// El tipo User se mantiene igual
export type User = {
  id: number; // Es importante tener el ID para el futuro
  username: string;
  email: string;
  dni: number;
  firstname: string;
  lastname: string;
  address: string | null;
  barrio: string | null;
  city: string | null;
  phone: string | null;
  phone2: string | null;
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

  // --- CORRECCIÓN DEFINITIVA AQUÍ ---
  // Accedemos directamente al token desde el hook, como debe ser.
  const { token } = useAuth();

  useEffect(() => {
    // La lógica de fetch se mantiene, ahora usando el 'token' corregido
    if (!token) {
      setIsLoading(false);
      return;
    }

    const fetchUsers = async () => {
      setIsLoading(true);
      setError(null);
      let url = `http://localhost:8000/api/admin/users/all?page=${currentPage}&size=10`;
      if (searchTerm) {
        url += `&username=${searchTerm}`;
      }

      try {
        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "No se pudieron cargar los usuarios."
          );
        }
        const data = await response.json();
        setUsers(data.items);
        setTotalPages(data.total_pages);
      } catch (err: any) {
        setError(err.message);
        setUsers([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsers();
  }, [currentPage, searchTerm, token]);

  const handleSearch = (term: string) => {
    setCurrentPage(1);
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

        {totalPages > 1 && (
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
