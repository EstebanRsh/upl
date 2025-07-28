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
          <Route path="/login" element={<Login />} />

          <Route element={<ProtectedRoutes />}>
            <Route element={<MainLayout />}>
              {/* Rutas para Clientes */}
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/payments" element={<PaymentHistory />} />
              <Route path="/profile" element={<Profile />} />
              <Route
                path="/services"
                element={<Placeholder title="Mis Servicios" />}
              />

              {/* Sección de Rutas para Admin */}
              <Route path="/admin" element={<AdminRoutes />}>
                <Route path="dashboard" element={<AdminDashboard />} />
                <Route path="clients" element={<ClientManagement />} />
                <Route
                  path="invoices"
                  element={<Placeholder title="Gestionar Facturas" />}
                />
              </Route>

              <Route path="/" element={<Navigate to="/dashboard" />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
