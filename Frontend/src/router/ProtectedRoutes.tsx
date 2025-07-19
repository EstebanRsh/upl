import { Navigate, Outlet } from "react-router-dom";

function ProtectedRoutes() {
  const token = localStorage.getItem("token");
  // Si no hay token, lo redirige al login
  if (!token) {
    return <Navigate to="/login" />;
  }
  // Si hay token, muestra el contenido de la ruta hija (Dashboard, etc.)
  return <Outlet />;
}

export default ProtectedRoutes;
