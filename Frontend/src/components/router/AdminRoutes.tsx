// src/routes/AdminRoutes.tsx
import { useContext } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { Spinner, Center } from "@chakra-ui/react";

const AdminRoutes = () => {
  const { user, loading } = useContext(AuthContext);

  // 1. Mientras se verifica el estado de autenticación, mostramos un spinner.
  //    Esto previene un parpadeo o redirección momentánea antes de tener la info del usuario.
  if (loading) {
    return (
      <Center height="100vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  // 2. Una vez que la carga ha terminado, verificamos si el usuario
  //    existe y si su rol es "administrador".
  if (user && user.role === "administrador") {
    // Si es un admin, le damos acceso a las rutas anidadas (las que protege este componente).
    return <Outlet />;
  }

  // 3. Si no está cargando y no es un admin, lo redirigimos al dashboard principal.
  //    El prop 'replace' evita que el usuario pueda volver a la página de admin con el botón "atrás".
  return <Navigate to="/dashboard" replace />;
};

export default AdminRoutes;
