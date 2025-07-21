import { useRef, useState } from "react";
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Text,
  useColorModeValue,
} from "@chakra-ui/react";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();
  const formBg = useColorModeValue("gray.100", "gray.700");

  // Usamos useRef para obtener el valor de los inputs solo al enviar el formulario.
  // Es eficiente porque no causa re-renders mientras el usuario escribe[cite: 147].
  const userInputRef = useRef<HTMLInputElement>(null);
  const passInputRef = useRef<HTMLInputElement>(null);

  // Usamos useState para manejar los mensajes de error o éxito[cite: 269].
  // Es la forma correcta en React, en lugar de manipular el DOM directamente[cite: 267].
  const [message, setMessage] = useState<string | null>(null);

  // Esta función se ejecuta cuando el usuario envía el formulario.
  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage(null); // Limpia el mensaje anterior

    const username = userInputRef.current?.value ?? "";
    const password = passInputRef.current?.value ?? "";

    // Valida que los campos no estén vacíos antes de enviar
    if (!username || !password) {
      setMessage("Por favor, completa ambos campos.");
      return;
    }

    // --- Conexión Real con el Backend ---
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const body = JSON.stringify({ username, password });

    const requestOptions = {
      method: "POST",
      headers: myHeaders,
      body: body,
    };

    try {
      // Apuntamos a la URL de tu backend. Asegúrate de que sea la correcta.
      const response = await fetch(
        "http://127.0.0.1:8000/api/users/login",
        requestOptions
      );
      const data = await response.json();

      if (response.ok && data.success) {
        setMessage("Iniciando sesión...");
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        navigate("/dashboard");
      } else {
        // Usa el mensaje de error del backend si existe, si no, uno genérico.
        setMessage(data.message || "Usuario o contraseña incorrectos.");
      }
    } catch (error) {
      console.error("Error al conectar con el servidor:", error);
      setMessage(
        "No se pudo conectar con el servidor. Revisa que el backend esté funcionando."
      );
    }
    // --- Fin de la conexión ---
  };

  return (
    <Flex
      align="center"
      justify="center"
      h="100vh"
      bg={useColorModeValue("gray.50", "gray.800")}
    >
      <Box bg={formBg} p={8} rounded="xl" shadow="lg" maxW="md" w="full">
        <VStack spacing={4}>
          <Heading color="brand.500">Bienvenido</Heading>
          <Text>Ingresa a tu cuenta para continuar</Text>
          <form onSubmit={handleLogin} style={{ width: "100%" }}>
            <VStack spacing={6} mt={4}>
              <FormControl isRequired>
                <FormLabel>Usuario</FormLabel>
                <Input type="text" ref={userInputRef} placeholder="ej: admin" />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Contraseña</FormLabel>
                <Input
                  type="password"
                  ref={passInputRef}
                  placeholder="ej: 1234"
                />
              </FormControl>
              <Button type="submit" colorScheme="brand" w="full" size="lg">
                Ingresar
              </Button>
              {message && (
                <Text
                  color={
                    message.includes("incorrectos") ? "red.500" : "green.500"
                  }
                >
                  {message}
                </Text>
              )}
            </VStack>
          </form>
        </VStack>
      </Box>
    </Flex>
  );
}

export default Login;
