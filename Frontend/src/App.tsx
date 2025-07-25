import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Box, Spinner } from "@chakra-ui/react";

// Layouts y Rutas
import MainLayout from "./components/layouts/MainLayout";
import ProtectedRoutes from "./components/router/ProtectedRoutes";

// Vistas
const Login = lazy(() => import("./components/Login"));
const Dashboard = lazy(() => import("./views/Dashboard"));
const PaymentHistory = lazy(() => import("./views/PaymentHistory"));
const Profile = lazy(() => import("./views/Profile"));

function App() {
  return (
    <BrowserRouter>
      <Suspense
        fallback={
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            height="100vh"
          >
            <Spinner size="xl" />
          </Box>
        }
      >
        <Routes>
          {/* Ruta pública para el Login */}
          <Route path="/login" element={<Login />} />

          {/* --- RUTAS PROTEGIDAS --- */}
          {/* El guardián 'ProtectedRoutes' envuelve a las vistas privadas */}
          <Route element={<ProtectedRoutes />}>
            {/* El 'MainLayout' provee la Navbar y el marco para las vistas */}
            <Route element={<MainLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/payments" element={<PaymentHistory />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Route>

          {/* Redirección inicial: si el usuario va a la raíz, lo mandamos al login */}
          <Route path="/" element={<Login />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
