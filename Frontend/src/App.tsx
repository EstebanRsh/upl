// src/App.tsx
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Box, Spinner, Heading, Text } from "@chakra-ui/react";

// Layouts y Rutas
import MainLayout from "./components/layouts/MainLayout";
import ProtectedRoutes from "./components/router/ProtectedRoutes";
import AdminRoutes from "./components/router/AdminRoutes";

// Vistas
const Login = lazy(() => import("./components/Login"));
const Dashboard = lazy(() => import("./views/Dashboard"));
const PaymentHistory = lazy(() => import("./views/PaymentHistory"));
const Profile = lazy(() => import("./views/Profile"));
const AdminDashboard = lazy(() => import("./views/admin/AdminDashboard"));
const ClientManagement = lazy(() => import("./views/admin/ClientManagement"));

// Componente genérico para vistas en desarrollo
const Placeholder = ({ title }: { title: string }) => (
  <Box p={8}>
    <Heading>{title}</Heading>
    <Text mt={4}>Página en construcción.</Text>
  </Box>
);

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
          {/* Ruta pública para el login */}
          <Route path="/login" element={<Login />} />

          {/* Aquí comienzan las rutas protegidas que requieren iniciar sesión */}
          <Route element={<ProtectedRoutes />}>
            <Route element={<MainLayout />}>
              {/* --- Rutas para Clientes --- */}
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/payments" element={<PaymentHistory />} />
              <Route path="/profile" element={<Profile />} />
              <Route
                path="/services"
                element={<Placeholder title="Mis Servicios" />}
              />

              {/* --- Sección de Rutas para Admin y Gerente --- */}
              {/* 1. La ruta base es "/admin" y está protegida por AdminRoutes */}
              <Route path="/admin" element={<AdminRoutes />}>
                {/* 2. Estas rutas se anidan DENTRO de /admin */}
                <Route path="dashboard" element={<AdminDashboard />} />
                <Route path="clients" element={<ClientManagement />} />
                <Route
                  path="invoices"
                  element={<Placeholder title="Gestionar Facturas" />}
                />
                <Route
                  path="settings"
                  element={<Placeholder title="Configuración" />}
                />
              </Route>

              {/* Redirección por defecto si se accede a la raíz "/" */}
              <Route path="/" element={<Navigate to="/dashboard" />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
