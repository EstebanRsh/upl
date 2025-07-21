import { BrowserRouter, Routes, Route } from "react-router-dom";
import PublicRoutes from "./components/router/PublicRoutes";
import ProtectedRoutes from "./components/router/ProtectedRoutes";
import Login from "./components/Login"; // Lo crearemos en el siguiente paso

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas Públicas */}
        <Route element={<PublicRoutes />}>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Login />} />{" "}
          {/* Ruta raíz también lleva al login */}
        </Route>

        {/* Rutas Protegidas (Aquí agregarás tu Dashboard, etc.) */}
        <Route element={<ProtectedRoutes />}>
          {/* Ejemplo: <Route path="/dashboard" element={<Dashboard />} /> */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
