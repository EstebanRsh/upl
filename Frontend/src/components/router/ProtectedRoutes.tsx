import { Navigate, Outlet } from "react-router-dom";

function ProtectedRoutes() {
  const token = localStorage.getItem("token");

  // Si no hay token, redirige al login.
  if (!token) {
    return <Navigate to="/login" />;
  }

  // Si hay token, muestra la ruta protegida que se solicitó.
  return <Outlet />;
}

export default ProtectedRoutes;
