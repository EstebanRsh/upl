import { Navigate, Outlet } from "react-router-dom";

function PublicRoutes() {
  const token = localStorage.getItem("token");

  // Si el token existe, no dejes que el usuario vea el login de nuevo.
  if (token) {
    return <Navigate to="/dashboard" />;
  }

  // Si no hay token, muestra la ruta que se solicitó (en este caso, el Login).
  return <Outlet />;
}

export default PublicRoutes;
