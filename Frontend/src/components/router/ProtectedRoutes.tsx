// src/components/router/ProtectedRoutes.tsx
import { useContext } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { Spinner, Center } from "@chakra-ui/react"; // O tu componente de carga preferido

const ProtectedRoutes = () => {
  const { user, loading } = useContext(AuthContext);

  // 1. Mientras el AuthContext está verificando el token (al cargar la página),
  //    mostramos un spinner. Esto es crucial para evitar redirecciones prematuras.
  if (loading) {
    return (
      <Center height="100vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  // 2. Una vez que la carga ha finalizado, verificamos si hay un usuario.
  //    Si lo hay, permitimos el acceso a las rutas anidadas (Dashboard, etc.).
  if (user) {
    return <Outlet />;
  }

  // 3. Si no está cargando y NO hay usuario, entonces redirigimos al login.
  return <Navigate to="/login" replace />;
};

export default ProtectedRoutes;
