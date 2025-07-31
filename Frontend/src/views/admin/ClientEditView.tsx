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
} from "@chakra-ui/react";
import { useAuth } from "../../context/AuthContext";
import {
  getUserById,
  updateUserDetails,
  UserDetail,
} from "../../services/adminService";

function ClientEditView() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const toast = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserDetail | null>(null);

  useEffect(() => {
    if (userId && token) {
      // Convertimos el userId a número para la llamada a la API
      const numericUserId = Number(userId);
      if (isNaN(numericUserId)) {
        setError("El ID del usuario en la URL no es válido.");
        setIsLoading(false);
        return;
      }

      getUserById(numericUserId, token)
        .then((data) => setUser(data))
        .catch((err) => {
          // --- CORRECCIÓN AQUÍ ---
          // Extraemos solo el mensaje de texto del error.
          const errorMessage =
            err.response?.data?.detail || "No se pudo cargar el cliente.";
          setError(errorMessage);
        })
        .finally(() => setIsLoading(false));
    }
  }, [userId, token]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setUser((prev) => (prev ? { ...prev, [name]: value } : null));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !user || !user.id) return;

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

  if (isLoading)
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <Spinner size="xl" />
      </Box>
    );

  // El error ahora es un string y se puede renderizar de forma segura
  if (error)
    return (
      <Alert status="error" mt={4}>
        <AlertIcon />
        {error}
      </Alert>
    );

  return (
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
              <Heading size="md">Datos de @{user.username}</Heading>
            </CardHeader>
            <CardBody>
              <Box as="form" onSubmit={handleSave}>
                <VStack spacing={4}>
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
                    <Button onClick={() => navigate("/admin/clients")} flex={1}>
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
  );
}

export default ClientEditView;
