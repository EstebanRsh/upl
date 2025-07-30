// src/views/admin/ClientManagement.tsx
import { useState, useEffect, useContext } from "react";
import {
  Box,
  Heading,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  HStack,
  Button,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  Input,
} from "@chakra-ui/react";
import { AuthContext } from "../../context/AuthContext";
import { ClientList } from "../../components/admin/ClientList";
import { ClientSearch } from "../../components/admin/ClientSearch";
import { Pagination } from "../../components/payments/Pagination";

export type User = {
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

type NewUserData = {
  username: string;
  email: string;
  password: string;
  dni: number;
  firstname: string;
  lastname: string;
  address: string;
  barrio: string;
  city: string;
  phone: string;
  phone2: string;
};

function ClientManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const { token } = useContext(AuthContext);
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  // Estado para el formulario de nuevo cliente
  const [newUser, setNewUser] = useState<NewUserData>({
    username: "",
    email: "",
    password: "",
    dni: 0,
    firstname: "",
    lastname: "",
    address: "",
    barrio: "",
    city: "",
    phone: "",
    phone2: "",
  });

  const fetchUsers = async () => {
    setIsLoading(true);
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
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUsers();
    }
  }, [currentPage, searchTerm, token]);

  const handleSearch = (term: string) => {
    setCurrentPage(1);
    setSearchTerm(term);
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();

    if (
      !newUser.username ||
      !newUser.email ||
      !newUser.password ||
      !newUser.dni
    ) {
      toast({
        title: "Error",
        description: "Los campos marcados como requeridos son obligatorios.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    try {
      const response = await fetch(
        "http://localhost:8000/api/admin/users/add",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(newUser),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Error al crear el usuario.");
      }

      toast({
        title: "Cliente agregado",
        description: "El nuevo cliente ha sido creado exitosamente.",
        status: "success",
        duration: 5000,
        isClosable: true,
      });

      // Resetear formulario y cerrar modal
      setNewUser({
        username: "",
        email: "",
        password: "",
        dni: 0,
        firstname: "",
        lastname: "",
        address: "",
        barrio: "",
        city: "",
        phone: "",
        phone2: "",
      });
      onClose();
      fetchUsers(); // Recargar la lista
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const renderContent = () => {
    if (isLoading)
      return (
        <Box display="flex" justifyContent="center" py={10}>
          <Spinner size="xl" />
        </Box>
      );
    if (error)
      return (
        <Alert status="error" mt={4}>
          <AlertIcon />
          {error}
        </Alert>
      );

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
        <Heading as="h1" size="xl">
          Gestión de Clientes
        </Heading>

        <HStack justify="space-between" wrap="wrap" gap={4}>
          <ClientSearch onSearch={handleSearch} />
          <Button colorScheme="teal" onClick={onOpen}>
            Nuevo Cliente
          </Button>
        </HStack>

        {renderContent()}

        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          isLoading={isLoading}
        />
      </VStack>

      {/* Modal para agregar nuevo cliente */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent bg="gray.700" color="white">
          <ModalHeader>Agregar Nuevo Cliente</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <Box as="form" onSubmit={handleAddUser}>
              <VStack spacing={4}>
                <HStack spacing={4} w="100%">
                  <FormControl isRequired>
                    <FormLabel>Nombre de Usuario</FormLabel>
                    <Input
                      value={newUser.username}
                      onChange={(e) =>
                        setNewUser({ ...newUser, username: e.target.value })
                      }
                    />
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>DNI</FormLabel>
                    <Input
                      type="number"
                      value={newUser.dni || ""}
                      onChange={(e) =>
                        setNewUser({
                          ...newUser,
                          dni: parseInt(e.target.value) || 0,
                        })
                      }
                    />
                  </FormControl>
                </HStack>

                <HStack spacing={4} w="100%">
                  <FormControl isRequired>
                    <FormLabel>Nombre</FormLabel>
                    <Input
                      value={newUser.firstname}
                      onChange={(e) =>
                        setNewUser({ ...newUser, firstname: e.target.value })
                      }
                    />
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>Apellido</FormLabel>
                    <Input
                      value={newUser.lastname}
                      onChange={(e) =>
                        setNewUser({ ...newUser, lastname: e.target.value })
                      }
                    />
                  </FormControl>
                </HStack>

                <FormControl isRequired>
                  <FormLabel>Email</FormLabel>
                  <Input
                    type="email"
                    value={newUser.email}
                    onChange={(e) =>
                      setNewUser({ ...newUser, email: e.target.value })
                    }
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Contraseña</FormLabel>
                  <Input
                    type="password"
                    value={newUser.password}
                    onChange={(e) =>
                      setNewUser({ ...newUser, password: e.target.value })
                    }
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Dirección</FormLabel>
                  <Input
                    value={newUser.address}
                    onChange={(e) =>
                      setNewUser({ ...newUser, address: e.target.value })
                    }
                  />
                </FormControl>

                <HStack spacing={4} w="100%">
                  <FormControl>
                    <FormLabel>Barrio</FormLabel>
                    <Input
                      value={newUser.barrio}
                      onChange={(e) =>
                        setNewUser({ ...newUser, barrio: e.target.value })
                      }
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Ciudad</FormLabel>
                    <Input
                      value={newUser.city}
                      onChange={(e) =>
                        setNewUser({ ...newUser, city: e.target.value })
                      }
                    />
                  </FormControl>
                </HStack>

                <HStack spacing={4} w="100%">
                  <FormControl>
                    <FormLabel>Teléfono Principal</FormLabel>
                    <Input
                      value={newUser.phone}
                      onChange={(e) =>
                        setNewUser({ ...newUser, phone: e.target.value })
                      }
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Teléfono Secundario</FormLabel>
                    <Input
                      value={newUser.phone2}
                      onChange={(e) =>
                        setNewUser({ ...newUser, phone2: e.target.value })
                      }
                    />
                  </FormControl>
                </HStack>

                <HStack spacing={4} w="100%" pt={4}>
                  <Button colorScheme="gray" onClick={onClose} flex={1}>
                    Cancelar
                  </Button>
                  <Button colorScheme="teal" type="submit" flex={1}>
                    Crear Cliente
                  </Button>
                </HStack>
              </VStack>
            </Box>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}

export default ClientManagement;
