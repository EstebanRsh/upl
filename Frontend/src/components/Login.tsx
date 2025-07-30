// src/components/Login.tsx
import { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext, User } from "../context/AuthContext";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Alert,
  AlertIcon,
  InputGroup,
  InputRightElement,
} from "@chakra-ui/react";

// Definimos el tipo de la respuesta que esperamos del backend
type LoginResponse = {
  success?: boolean;
  access_token?: string;
  user?: User; // Usamos la interfaz User de nuestro AuthContext
  detail?: string; // Para los mensajes de error
};

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const auth = useContext(AuthContext); // Obtenemos el contexto de autenticación

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/api/users/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data: LoginResponse = await response.json();

      // Verificación más estricta de la respuesta
      if (!response.ok || !data.success || !data.access_token || !data.user) {
        throw new Error(
          data.detail ||
            "Credenciales incorrectas o respuesta inválida del servidor."
        );
      }

      // --- ¡ESTA ES LA CORRECCIÓN CLAVE! ---
      // Usamos la función 'login' del AuthContext para manejar el estado.
      // Esta función se encarga de actualizar el estado y guardar en localStorage.
      auth.login(data.access_token, data.user);

      // Ahora que el estado está actualizado, redirigimos.
      // El rol se verificará en el componente Dashboard.
      navigate("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Ocurrió un error inesperado."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      bg="gray.800"
    >
      <Box
        p={8}
        maxWidth="400px"
        width="100%"
        bg="gray.700"
        color="white"
        borderWidth={1}
        borderColor="gray.600"
        borderRadius={8}
        boxShadow="lg"
      >
        <VStack as="form" onSubmit={handleSubmit} spacing={4}>
          <Heading>Iniciar Sesión</Heading>
          {error && (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              {error}
            </Alert>
          )}
          <FormControl isRequired>
            <FormLabel>Usuario</FormLabel>
            <Input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              bg="gray.600"
              border="none"
            />
          </FormControl>
          <FormControl isRequired>
            <FormLabel>Contraseña</FormLabel>
            <InputGroup>
              <Input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                bg="gray.600"
                border="none"
              />
              <InputRightElement width="4.5rem">
                <Button
                  h="1.75rem"
                  size="sm"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? "Ocultar" : "Mostrar"}
                </Button>
              </InputRightElement>
            </InputGroup>
          </FormControl>
          <Button
            type="submit"
            colorScheme="teal"
            width="full"
            isLoading={loading}
          >
            Ingresar
          </Button>
        </VStack>
      </Box>
    </Box>
  );
};

export default Login;
