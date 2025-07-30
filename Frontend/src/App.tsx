// src/App.tsx
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Box, Spinner, Heading, Text } from "@chakra-ui/react";
import { AuthProvider } from "./context/AuthContext"; // <-- 1. Importamos el AuthProvider

// Layouts y Rutas
import MainLayout from "./components/layouts/MainLayout";
import ProtectedRoutes from "./components/router/ProtectedRoutes";
import AdminRoutes from "./components/router/AdminRoutes";
import InvoiceManagement from "./views/admin/InvoiceManagement";
import InvoiceDetailView from "./views/admin/InvoiceDetailView";
import ClientInvoiceDetailView from "./views/client/ClientInvoiceDetailView";
import ClientEditView from "./views/admin/ClientEditView";
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
    // 2. Envolvemos el BrowserRouter con AuthProvider
    <AuthProvider>
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
                <Route
                  path="/payments/:invoiceId"
                  element={<ClientInvoiceDetailView />}
                />
                <Route path="/profile" element={<Profile />} />
                <Route
                  path="/services"
                  element={<Placeholder title="Mis Servicios" />}
                />

                {/* --- Sección de Rutas para Admin --- */}
                <Route path="/admin" element={<AdminRoutes />}>
                  {/* Estas rutas se anidan DENTRO de /admin */}
                  <Route path="dashboard" element={<AdminDashboard />} />
                  <Route path="clients" element={<ClientManagement />} />
                  <Route
                    path="clients/:dni/edit"
                    element={<ClientEditView />}
                  />
                  <Route path="invoices" element={<InvoiceManagement />} />
                  <Route
                    path="invoices/:invoiceId"
                    element={<InvoiceDetailView />}
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

            {/* Redirección final si no coincide nada */}
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
