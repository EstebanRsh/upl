// src/views/admin/ClientEditView.tsx
import { useState, useEffect, useContext } from "react";
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
  Spinner,
  Alert,
  AlertIcon,
  Card,
  CardBody,
  CardHeader,
} from "@chakra-ui/react";
import { AuthContext } from "../../context/AuthContext";

type UserDetail = {
  dni: number;
  firstname: string;
  lastname: string;
  address: string | null;
  barrio: string | null;
  city: string | null;
  phone: string | null;
  phone2: string | null;
};

function ClientEditView() {
  const { dni } = useParams<{ dni: string }>();
  const navigate = useNavigate();
  const { token } = useContext(AuthContext);
  const toast = useToast();

  const [userDetail, setUserDetail] = useState<UserDetail>({
    dni: 0,
    firstname: "",
    lastname: "",
    address: "",
    barrio: "",
    city: "",
    phone: "",
    phone2: "",
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Buscar el usuario por DNI en la lista existente
  useEffect(() => {
    const fetchUserByDni = async () => {
      if (!dni || !token) return;

      try {
        setIsLoading(true);
        // Buscar en la lista de usuarios por DNI
        const response = await fetch(
          `http://localhost:8000/api/admin/users/all?page=1&size=100`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Error al cargar el usuario.");
        }

        const data = await response.json();
        const user = data.items.find((u: any) => u.dni.toString() === dni);

        if (!user) {
          throw new Error("Usuario no encontrado.");
        }

        setUserDetail({
          dni: user.dni,
          firstname: user.firstname,
          lastname: user.lastname,
          address: user.address,
          barrio: user.barrio,
          city: user.city,
          phone: user.phone,
          phone2: user.phone2,
        });
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserByDni();
  }, [dni, token]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      // Necesitarías encontrar el user_id del usuario para hacer el update
      // Por ahora usamos un endpoint hipotético
      const response = await fetch(
        `http://localhost:8000/api/admin/users/by-dni/${dni}/details`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(userDetail),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Error al actualizar el usuario.");
      }

      toast({
        title: "Usuario actualizado",
        description:
          "Los datos del cliente han sido actualizados exitosamente.",
        status: "success",
        duration: 5000,
        isClosable: true,
      });

      navigate("/admin/clients");
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <Spinner size="xl" />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={{ base: 4, md: 8 }}>
        <Alert status="error">
          <AlertIcon />
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      p={{ base: 4, md: 8 }}
      bg="gray.800"
      color="white"
      minH="calc(100vh - 4rem)"
    >
      <VStack spacing={6} align="stretch" maxW="800px" mx="auto">
        <HStack justify="space-between">
          <Heading as="h1" size="xl">
            Editar Cliente
          </Heading>
          <Button onClick={() => navigate("/admin/clients")}>
            Volver a la lista
          </Button>
        </HStack>

        <Card bg="gray.700" color="white">
          <CardHeader>
            <Heading size="md">Información del Cliente</Heading>
          </CardHeader>
          <CardBody>
            <Box as="form" onSubmit={handleSave}>
              <VStack spacing={4}>
                <HStack spacing={4} w="100%">
                  <FormControl isRequired>
                    <FormLabel>DNI</FormLabel>
                    <Input
                      type="number"
                      value={userDetail.dni || ""}
                      onChange={(e) =>
                        setUserDetail({
                          ...userDetail,
                          dni: parseInt(e.target.value) || 0,
                        })
                      }
                      isDisabled // El DNI no debería cambiar
                    />
                  </FormControl>
                </HStack>

                <HStack spacing={4} w="100%">
                  <FormControl isRequired>
                    <FormLabel>Nombre</FormLabel>
                    <Input
                      value={userDetail.firstname}
                      onChange={(e) =>
                        setUserDetail({
                          ...userDetail,
                          firstname: e.target.value,
                        })
                      }
                    />
                  </FormControl>
                  <FormControl isRequired>
                    <FormLabel>Apellido</FormLabel>
                    <Input
                      value={userDetail.lastname}
                      onChange={(e) =>
                        setUserDetail({
                          ...userDetail,
                          lastname: e.target.value,
                        })
                      }
                    />
                  </FormControl>
                </HStack>

                <FormControl>
                  <FormLabel>Dirección</FormLabel>
                  <Input
                    value={userDetail.address || ""}
                    onChange={(e) =>
                      setUserDetail({ ...userDetail, address: e.target.value })
                    }
                  />
                </FormControl>

                <HStack spacing={4} w="100%">
                  <FormControl>
                    <FormLabel>Barrio</FormLabel>
                    <Input
                      value={userDetail.barrio || ""}
                      onChange={(e) =>
                        setUserDetail({ ...userDetail, barrio: e.target.value })
                      }
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Ciudad</FormLabel>
                    <Input
                      value={userDetail.city || ""}
                      onChange={(e) =>
                        setUserDetail({ ...userDetail, city: e.target.value })
                      }
                    />
                  </FormControl>
                </HStack>

                <HStack spacing={4} w="100%">
                  <FormControl>
                    <FormLabel>Teléfono Principal</FormLabel>
                    <Input
                      value={userDetail.phone || ""}
                      onChange={(e) =>
                        setUserDetail({ ...userDetail, phone: e.target.value })
                      }
                    />
                  </FormControl>
                  <FormControl>
                    <FormLabel>Teléfono Secundario</FormLabel>
                    <Input
                      value={userDetail.phone2 || ""}
                      onChange={(e) =>
                        setUserDetail({ ...userDetail, phone2: e.target.value })
                      }
                    />
                  </FormControl>
                </HStack>

                <HStack spacing={4} w="100%" pt={4}>
                  <Button
                    colorScheme="gray"
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
                    loadingText="Guardando..."
                  >
                    Guardar Cambios
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

export default ClientEditView;
