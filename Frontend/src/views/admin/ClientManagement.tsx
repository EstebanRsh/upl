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
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
} from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";
import { ClientSearch } from "../../components/admin/ClientSearch";
import { Pagination } from "../../components/payments/Pagination"; // Reutilizamos la paginación

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

  const getRoleBadge = (role: string) => {
    const roles = {
      Admin: "red",
      Gerente: "pink",
      Técnico: "blue",
      Cobrador: "green",
      Cliente: "purple",
    };
    return (
      <Badge colorScheme={roles[role as keyof typeof roles] || "gray"}>
        {role}
      </Badge>
    );
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
    if (users.length === 0) {
      return (
        <Box bg="gray.700" p={6} borderRadius="md" textAlign="center">
          <Text color="gray.400">
            No se encontraron clientes con los criterios de búsqueda.
          </Text>
        </Box>
      );
    }
    return (
      <TableContainer bg="gray.700" borderRadius="md">
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th color="white">Nombre Completo</Th>
              <Th color="white">Usuario</Th>
              <Th color="white">DNI</Th>
              <Th color="white">Email</Th>
              <Th color="white">Rol</Th>
              <Th color="white">Acciones</Th>
            </Tr>
          </Thead>
          <Tbody>
            {users.map((user) => (
              <Tr key={user.dni}>
                <Td>
                  {user.firstname} {user.lastname}
                </Td>
                <Td>@{user.username}</Td>
                <Td>{user.dni}</Td>
                <Td>{user.email}</Td>
                <Td>{getRoleBadge(user.role)}</Td>
                <Td>
                  <Button
                    size="sm"
                    colorScheme="blue"
                    onClick={() => navigate(`/admin/clients/${user.dni}/edit`)}
                  >
                    Editar
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </TableContainer>
    );
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

        {renderContent()}

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
