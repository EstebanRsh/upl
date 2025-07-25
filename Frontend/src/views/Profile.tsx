// src/views/Profile.tsx
import { useState, useEffect } from "react";
import {
  Box,
  Heading,
  Text,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  FormControl,
  FormLabel,
  Input,
  Button,
  useToast,
  Grid,
  Card,
  CardBody,
  Icon,
  Avatar,
  HStack,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  CardHeader,
} from "@chakra-ui/react";
import {
  FaMapMarkerAlt,
  FaPhone,
  FaEnvelope,
  FaIdCard,
  FaKey,
} from "react-icons/fa";

// El tipo de dato para el perfil
type UserProfile = {
  firstname: string;
  lastname: string;
  username: string;
  email: string;
  dni: number;
  address: string | null;
  barrio: string | null;
  city: string | null;
  phone: string | null;
  phone2: string | null;
};

// Componente para mostrar un detalle del perfil
const ProfileDetail = ({
  icon,
  label,
  value,
}: {
  icon: any;
  label: string;
  value: string | number | null;
}) => (
  <HStack spacing={4} w="100%">
    <Icon as={icon} color="teal.300" boxSize={5} />
    <Box>
      <Text fontSize="sm" color="gray.400">
        {label}
      </Text>
      <Text fontSize="md" fontWeight="medium">
        {value || "No especificado"}
      </Text>
    </Box>
  </HStack>
);

function Profile() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);

  useEffect(() => {
    // La lógica de fetch no ha cambiado
    const fetchUserData = async () => {
      const token = localStorage.getItem("token");
      const USER_ME_URL = "http://localhost:8000/api/users/me";
      try {
        if (!token) throw new Error("No se encontró token de sesión.");
        const response = await fetch(USER_ME_URL, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "No se pudieron cargar los datos del perfil."
          );
        }
        const data = await response.json();
        setUser(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    fetchUserData();
  }, []);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast({
        title: "Contraseña inválida",
        description: "La nueva contraseña debe tener al menos 8 caracteres.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return;
    }
    // La lógica de cambio de contraseña no ha cambiado
    setIsPasswordLoading(true);
    const token = localStorage.getItem("token");
    const CHANGE_PASSWORD_URL = "http://localhost:8000/api/users/me/password";
    try {
      const response = await fetch(CHANGE_PASSWORD_URL, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Error al cambiar la contraseña.");
      }
      toast({
        title: "Contraseña actualizada.",
        status: "success",
        duration: 5000,
        isClosable: true,
      });
      setCurrentPassword("");
      setNewPassword("");
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsPasswordLoading(false);
    }
  };

  const formatAddress = (user: UserProfile) => {
    return [user.address, user.barrio, user.city].filter(Boolean).join(", ");
  };

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="80vh"
      >
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
  if (!user) {
    return (
      <Box p={{ base: 4, md: 8 }}>
        <Alert status="warning">
          <AlertIcon />
          No se pudieron mostrar los datos del perfil.
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
      <Grid
        templateColumns={{ base: "1fr", lg: "1fr 2fr" }}
        gap={{ base: 6, lg: 8 }}
        maxW="1200px"
        mx="auto"
        alignItems="start" // Alinea las columnas en la parte superior
      >
        {/* COLUMNA IZQUIERDA: TARJETA DE IDENTIDAD */}
        <Card
          bg="gray.700"
          color="white"
          p={4}
          position={{ lg: "sticky" }}
          top="6rem"
        >
          <CardBody>
            <VStack spacing={4}>
              <Avatar
                size="2xl"
                name={`${user.firstname} ${user.lastname}`}
                bg="teal.400"
              />
              <Box textAlign="center">
                <Heading size="lg">
                  {user.firstname} {user.lastname}
                </Heading>
                <Text color="gray.400">@{user.username}</Text>
              </Box>
            </VStack>
          </CardBody>
        </Card>

        {/* COLUMNA DERECHA: DETALLES Y SEGURIDAD */}
        <VStack spacing={6} align="stretch">
          <Card bg="gray.700" color="white">
            <CardHeader>
              <Heading size="md">Información de Contacto</Heading>
            </CardHeader>
            <CardBody>
              <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={6}>
                <ProfileDetail icon={FaIdCard} label="DNI" value={user.dni} />
                <ProfileDetail
                  icon={FaEnvelope}
                  label="Email"
                  value={user.email}
                />
                <ProfileDetail
                  icon={FaPhone}
                  label="Teléfono Principal"
                  value={user.phone}
                />
                <ProfileDetail
                  icon={FaPhone}
                  label="Teléfono Secundario"
                  value={user.phone2}
                />
                <ProfileDetail
                  icon={FaMapMarkerAlt}
                  label="Dirección Completa"
                  value={formatAddress(user)}
                />
              </Grid>
            </CardBody>
          </Card>

          <Card bg="gray.700" color="white">
            <Accordion allowToggle>
              <AccordionItem border="none">
                <h2>
                  <AccordionButton
                    _expanded={{ bg: "teal.500", color: "white" }}
                    borderRadius="md"
                  >
                    <HStack as="span" flex="1" textAlign="left">
                      <Icon as={FaKey} />
                      <Heading size="md">Seguridad</Heading>
                    </HStack>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel pb={4}>
                  <Box as="form" onSubmit={handlePasswordChange} mt={4}>
                    <VStack spacing={4} align="stretch">
                      <FormControl isRequired>
                        <FormLabel fontSize="sm">Contraseña Actual</FormLabel>
                        <Input
                          type="password"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                        />
                      </FormControl>
                      <FormControl isRequired>
                        <FormLabel fontSize="sm">Nueva Contraseña</FormLabel>
                        <Input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          placeholder="Mínimo 8 caracteres"
                        />
                      </FormControl>
                      <Button
                        type="submit"
                        colorScheme="teal"
                        alignSelf="flex-end"
                        isLoading={isPasswordLoading}
                      >
                        Actualizar Contraseña
                      </Button>
                    </VStack>
                  </Box>
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          </Card>
        </VStack>
      </Grid>
    </Box>
  );
}

export default Profile;
