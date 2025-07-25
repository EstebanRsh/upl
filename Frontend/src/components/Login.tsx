// src/components/Login.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  useToast,
  InputGroup,
  InputRightElement,
} from "@chakra-ui/react";

type LoginResponse = {
  success?: boolean;
  access_token?: string;
  detail?: string;
};

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();
  const LOGIN_URL = `http://localhost:8000/api/users/login`;

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch(LOGIN_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username, password: password }),
      });

      const data: LoginResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Error: ${response.statusText}`);
      }

      if (data.success && data.access_token) {
        localStorage.setItem("token", data.access_token);
        localStorage.removeItem("user");
        toast({
          title: "Inicio de sesión exitoso.",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
        navigate("/dashboard");
      } else {
        throw new Error("La respuesta del servidor no fue la esperada.");
      }
    } catch (error: any) {
      toast({
        title: "Error al iniciar sesión",
        description: error.message,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      height="100vh"
      bg="gray.100"
    >
      <Box bg="white" p={8} rounded="md" shadow="md" width="100%" maxW="md">
        <form onSubmit={handleLogin}>
          <VStack spacing={4}>
            <Heading as="h1" size="lg">
              Iniciar Sesión
            </Heading>
            <FormControl isRequired>
              <FormLabel htmlFor="username">Usuario</FormLabel>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel htmlFor="password">Contraseña</FormLabel>
              <InputGroup>
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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
              isLoading={isLoading}
            >
              Ingresar
            </Button>
          </VStack>
        </form>
      </Box>
    </Box>
  );
}
