import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import Dashboard from "./views/Dashboard";
import PublicRoutes from "./router/PublicRoutes";
import ProtectedRoutes from "./router/ProtectedRoutes";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas Públicas: solo accesibles si NO estás logueado */}
        <Route element={<PublicRoutes />}>
          <Route path="/" element={<Login />} />
          <Route path="/login" element={<Login />} />
        </Route>

        {/* Rutas Protegidas: solo accesibles si ESTÁS logueado */}
        <Route element={<ProtectedRoutes />}>
          <Route path="/dashboard" element={<Dashboard />} />
          {/* Aquí podrías agregar más rutas protegidas, como /perfil, /pagos, etc. */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
