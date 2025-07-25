// src/views/Profile.tsx
import { Box, Heading } from "@chakra-ui/react";

function Profile() {
  return (
    <Box p={8}>
      <Heading as="h1" size="xl">
        Mi Perfil
      </Heading>
      <Box mt={6}>
        <p>Esta página mostrará la información del perfil del usuario.</p>
        <p>¡Funcionalidad en desarrollo!</p>
      </Box>
    </Box>
  );
}

export default Profile;
