// src/views/admin/ClientEditView.tsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Heading,
  VStack,
  HStack,
  Button,
  FormControl,
  FormLabel,
  Input,
  useToast,
  Card,
  CardBody,
  CardHeader,
  Spinner,
  Alert,
  AlertIcon,
  useDisclosure, // <-- 1. Importamos el hook para el modal
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Text,
} from "@chakra-ui/react";
import { useAuth } from "../../context/AuthContext";
// Importamos la función 'deleteUser' que acabamos de verificar
import {
  getUserById,
  updateUserDetails,
  deleteUser, // <-- 2. Importamos la función de borrado
  UserDetail,
} from "../../services/adminService";

function ClientEditView() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const toast = useToast();
  // 3. Configuramos el controlador del modal
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserDetail | null>(null);

  useEffect(() => {
    if (userId && token) {
      getUserById(Number(userId), token)
        .then((data) => setUser(data))
        .catch((err) =>
          setError(
            err.response?.data?.detail || "No se pudo cargar el cliente."
          )
        )
        .finally(() => setIsLoading(false));
    }
  }, [userId, token]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setUser((prev) => (prev ? { ...prev, [name]: value } : null));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !user) return;
    // Lógica de guardado (sin cambios)
    setIsSaving(true);
    try {
      const { id, firstname, lastname, address, barrio, city, phone, phone2 } =
        user;
      await updateUserDetails(
        id,
        { firstname, lastname, address, barrio, city, phone, phone2 },
        token
      );
      toast({ title: "Cliente Actualizado", status: "success" });
      navigate("/admin/clients");
    } catch (err: any) {
      const errorDescription =
        err.response?.data?.detail || "Ocurrió un error.";
      toast({
        title: "Error al actualizar",
        description:
          typeof errorDescription === "string"
            ? errorDescription
            : JSON.stringify(errorDescription),
        status: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // 4. Creamos la función para manejar el borrado
  const handleDelete = async () => {
    if (!token || !user) return;

    setIsDeleting(true);
    try {
      await deleteUser(user.id, token);
      toast({
        title: "Cliente Eliminado",
        description: `El cliente @${user.username} ha sido eliminado.`,
        status: "warning",
      });
      navigate("/admin/clients");
    } catch (err: any) {
      const errorDescription =
        err.response?.data?.detail || "Ocurrió un error.";
      toast({
        title: "Error al eliminar",
        description:
          typeof errorDescription === "string"
            ? errorDescription
            : JSON.stringify(errorDescription),
        status: "error",
      });
      setIsDeleting(false);
    }
  };

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

  return (
    <>
      <Box p={{ base: 4, md: 8 }} bg="gray.800" color="white" minH="100vh">
        <VStack spacing={6} align="stretch" maxW="800px" mx="auto">
          <HStack justify="space-between">
            <Heading as="h1" size="xl">
              Editar Cliente
            </Heading>
            <Button onClick={() => navigate("/admin/clients")}>Volver</Button>
          </HStack>
          {user && (
            <Card bg="gray.700" color="white">
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">Datos de @{user.username}</Heading>
                  {/* 5. Añadimos el botón de eliminar, que abre el modal */}
                  <Button colorScheme="red" size="sm" onClick={onOpen}>
                    Eliminar Cliente
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody>
                <Box as="form" onSubmit={handleSave}>
                  <VStack spacing={4}>
                    {/* ... (todos los inputs del formulario quedan igual) ... */}
                    <HStack w="100%">
                      <FormControl isRequired>
                        <FormLabel>Nombre</FormLabel>
                        <Input
                          name="firstname"
                          value={user.firstname}
                          onChange={handleInputChange}
                        />
                      </FormControl>
                      <FormControl isRequired>
                        <FormLabel>Apellido</FormLabel>
                        <Input
                          name="lastname"
                          value={user.lastname}
                          onChange={handleInputChange}
                        />
                      </FormControl>
                    </HStack>
                    <FormControl>
                      <FormLabel>DNI</FormLabel>
                      <Input value={user.dni} isReadOnly bg="gray.600" />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Email</FormLabel>
                      <Input
                        type="email"
                        readOnly
                        value={user.email}
                        bg="gray.600"
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Dirección</FormLabel>
                      <Input
                        name="address"
                        value={user.address || ""}
                        onChange={handleInputChange}
                      />
                    </FormControl>
                    <HStack w="100%">
                      <FormControl>
                        <FormLabel>Barrio</FormLabel>
                        <Input
                          name="barrio"
                          value={user.barrio || ""}
                          onChange={handleInputChange}
                        />
                      </FormControl>
                      <FormControl>
                        <FormLabel>Ciudad</FormLabel>
                        <Input
                          name="city"
                          value={user.city || ""}
                          onChange={handleInputChange}
                        />
                      </FormControl>
                    </HStack>
                    <HStack w="100%">
                      <FormControl>
                        <FormLabel>Teléfono</FormLabel>
                        <Input
                          name="phone"
                          value={user.phone || ""}
                          onChange={handleInputChange}
                        />
                      </FormControl>
                      <FormControl>
                        <FormLabel>Teléfono 2</FormLabel>
                        <Input
                          name="phone2"
                          value={user.phone2 || ""}
                          onChange={handleInputChange}
                        />
                      </FormControl>
                    </HStack>

                    <HStack w="100%" pt={4}>
                      <Button
                        onClick={() => navigate("/admin/clients")}
                        flex={1}
                      >
                        Cancelar
                      </Button>
                      <Button
                        colorScheme="teal"
                        type="submit"
                        flex={1}
                        isLoading={isSaving}
                      >
                        Guardar Cambios
                      </Button>
                    </HStack>
                  </VStack>
                </Box>
              </CardBody>
            </Card>
          )}
        </VStack>
      </Box>

      {/* 6. Definimos el Modal de Confirmación */}
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent bg="gray.700" color="white">
          <ModalHeader>Confirmar Eliminación</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              ¿Estás seguro de que deseas eliminar al cliente{" "}
              <strong>
                {user?.firstname} {user?.lastname}
              </strong>
              ?
            </Text>
            <Text mt={2} color="red.300">
              Esta acción no se puede deshacer.
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancelar
            </Button>
            <Button
              colorScheme="red"
              isLoading={isDeleting}
              onClick={handleDelete}
            >
              Sí, Eliminar
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}

export default ClientEditView;
