// src/components/admin/ClientList.tsx
import {
  Box,
  Text,
  Badge,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
} from "@chakra-ui/react";
import { User } from "../../views/admin/ClientManagement";
import { useNavigate } from "react-router-dom";

interface ClientListProps {
  users: User[];
}

export const ClientList = ({ users }: ClientListProps) => {
  const navigate = useNavigate();

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
              <Td>
                <Badge colorScheme="purple">{user.role}</Badge>
              </Td>
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
