// src/App.tsx
import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Box, Spinner, Heading, Text } from "@chakra-ui/react";
import { AuthProvider } from "./context/AuthContext";

// Layouts y Rutas
import MainLayout from "./components/layouts/MainLayout";
import ProtectedRoutes from "./components/router/ProtectedRoutes";
import AdminRoutes from "./components/router/AdminRoutes";

// Vistas que no son lazy-loaded (pueden serlo si prefieres)
import InvoiceManagement from "./views/admin/InvoiceManagement";
import InvoiceDetailView from "./views/admin/InvoiceDetailView";
import ClientInvoiceDetailView from "./views/client/ClientInvoiceDetailView";
import ClientEditView from "./views/admin/ClientEditView";
import ClientAddView from "./views/admin/ClientAddView";
import RegisterPaymentView from "./views/admin/RegisterPaymentView";

// Vistas con carga perezosa (lazy-loading)
const Login = lazy(() => import("./components/Login"));
const Dashboard = lazy(() => import("./views/Dashboard"));
const PaymentHistory = lazy(() => import("./views/PaymentHistory"));
const Profile = lazy(() => import("./views/Profile"));
const AdminDashboard = lazy(() => import("./views/admin/AdminDashboard"));
const ClientManagement = lazy(() => import("./views/admin/ClientManagement"));
// --- 1. AÑADIMOS LA NUEVA VISTA DE GESTIÓN DE PAGOS A LA CARGA PEREZOSA ---
const PaymentManagement = lazy(() => import("./views/admin/PaymentManagement"));
const PlanManagement = lazy(() => import("./views/admin/PlanManagement"));
const SettingsView = lazy(() => import("./views/admin/SettingsView"));
// Componente genérico para vistas en desarrollo
const Placeholder = ({ title }: { title: string }) => (
  <Box p={8}>
    <Heading>{title}</Heading>
    <Text mt={4}>Página en construcción.</Text>
  </Box>
);

function App() {
  return (
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
            <Route path="/login" element={<Login />} />

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
                  <Route path="dashboard" element={<AdminDashboard />} />
                  <Route path="clients" element={<ClientManagement />} />
                  <Route path="clients/add" element={<ClientAddView />} />
                  <Route
                    path="clients/:userId/edit"
                    element={<ClientEditView />}
                  />
                  <Route path="invoices" element={<InvoiceManagement />} />
                  <Route
                    path="invoices/:invoiceId"
                    element={<InvoiceDetailView />}
                  />

                  {/* --- 2. AÑADIMOS LAS RUTAS DE PAGOS DEL ADMIN AQUÍ --- */}
                  <Route path="payments" element={<PaymentManagement />} />
                  <Route
                    path="payments/register"
                    element={<RegisterPaymentView />}
                  />
                  <Route path="plans" element={<PlanManagement />} />
                  <Route path="settings" element={<SettingsView />} />
                </Route>

                <Route path="/" element={<Navigate to="/dashboard" />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
