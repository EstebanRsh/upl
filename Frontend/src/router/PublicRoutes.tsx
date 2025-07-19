import { Navigate, Outlet } from "react-router-dom";

function PublicRoutes() {
  const token = localStorage.getItem("token");
  // Si hay un token, lo redirige al dashboard
  if (token) {
    return <Navigate to="/dashboard" />;
  }
  // Si no hay token, muestra la ruta pública (Login)
  return <Outlet />;
}

export default PublicRoutes;
