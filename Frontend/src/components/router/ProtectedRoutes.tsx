import { Navigate, Outlet } from "react-router-dom";

function ProtectedRoutes() {
  const token = localStorage.getItem("token");

  // Si no hay token, redirige a la página de login
  if (!token) {
    return <Navigate to="/login" />;
  }

  // Si hay un token, permite el acceso a las rutas anidadas (hijas)
  return <Outlet />;
}

export default ProtectedRoutes;
