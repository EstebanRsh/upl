// src/views/admin/ClientAddView.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
} from "@chakra-ui/react";
import { useAuth } from "../../context/AuthContext";
import { addUser } from "../../services/adminService";

export type NewUser = {
  username: string;
  password: "";
  email: string;
  dni: string;
  firstname: string;
  lastname: string;
  address: string;
  barrio: string;
  city: string;
  phone: string;
  phone2: string;
};

function ClientAddView() {
  const navigate = useNavigate();
  const { auth } = useAuth();
  const toast = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState<NewUser>({
    username: "",
    password: "",
    email: "",
    dni: "",
    firstname: "",
    lastname: "",
    address: "",
    barrio: "",
    city: "",
    phone: "",
    phone2: "",
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!auth.token) return;

    setIsSaving(true);
    try {
      await addUser(formData, auth.token);
      toast({
        title: "Cliente Creado",
        description: `El cliente ${formData.firstname} ${formData.lastname} ha sido añadido.`,
        status: "success",
      });
      navigate("/admin/clients");
    } catch (err: any) {
      // CORRECCIÓN: Nos aseguramos de que la descripción sea siempre un string.
      const errorDescription =
        err.response?.data?.detail || "Ocurrió un error inesperado.";
      toast({
        title: "Error al crear",
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

  return (
    <Box p={{ base: 4, md: 8 }} bg="gray.800" color="white" minH="100vh">
      <VStack spacing={6} align="stretch" maxW="800px" mx="auto">
        <HStack justify="space-between">
          <Heading as="h1" size="xl">
            Añadir Nuevo Cliente
          </Heading>
          <Button onClick={() => navigate("/admin/clients")}>Volver</Button>
        </HStack>
        <Card bg="gray.700" color="white">
          <CardHeader>
            <Heading size="md">Datos del Cliente</Heading>
          </CardHeader>
          <CardBody>
            <Box as="form" onSubmit={handleSave}>
              <VStack spacing={4}>
                <HStack w="100%">
                  <FormControl isRequired>
                    <FormLabel>Nombre</FormLabel>
                    <Input
                      name="firstname"
                      value={formData.firstname}
                      onChange={handleInputChange}
                    />
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>Apellido</FormLabel>
                    <Input
                      name="lastname"
                      value={formData.lastname}
                      onChange={handleInputChange}
                    />
                  </FormControl>
                </HStack>
                <FormControl isRequired>
                  <FormLabel>DNI</FormLabel>
                  <Input
                    name="dni"
                    value={formData.dni}
                    onChange={handleInputChange}
                  />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>Email</FormLabel>
                  <Input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                  />
                </FormControl>
                <HStack w="100%">
                  <FormControl isRequired>
                    <FormLabel>Usuario</FormLabel>
                    <Input
                      name="username"
                      value={formData.username}
                      onChange={handleInputChange}
                    />
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>Contraseña</FormLabel>
                    <Input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                    />
                  </FormControl>
                </HStack>
                <FormControl>
                  <FormLabel>Dirección</FormLabel>
                  <Input
                    name="address"
                    value={formData.address}
                    onChange={handleInputChange}
                  />
                </FormControl>
                <HStack w="100%">
                  <FormControl>
                    <FormLabel>Barrio</FormLabel>
                    <Input
                      name="barrio"
                      value={formData.barrio}
                      onChange={handleInputChange}
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Ciudad</FormLabel>
                    <Input
                      name="city"
                      value={formData.city}
                      onChange={handleInputChange}
                    />
                  </FormControl>
                </HStack>
                <HStack w="100%">
                  <FormControl>
                    <FormLabel>Teléfono</FormLabel>
                    <Input
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Teléfono 2</FormLabel>
                    <Input
                      name="phone2"
                      value={formData.phone2}
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
                    Guardar Cliente
                  </Button>
                </HStack>
              </VStack>
            </Box>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
}

export default ClientAddView;
