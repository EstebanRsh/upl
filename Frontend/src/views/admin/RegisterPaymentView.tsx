// src/views/admin/RegisterPaymentView.tsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Heading,
  VStack,
  HStack,
  Button,
  FormControl,
  FormLabel,
  Input,
  useToast,
  Card,
  CardBody,
  CardHeader,
  Spinner,
  Text,
  Select,
  SimpleGrid,
  Icon,
} from "@chakra-ui/react";
import { FaFileUpload } from "react-icons/fa";
import { useAuth } from "../../context/AuthContext";
import {
  UserDetail,
  Invoice,
  getPendingInvoicesByUserId,
  registerManualPayment,
} from "../../services/adminService";
import { ClientSearch } from "../../components/admin/ClientSearch"; // Reutilizamos el buscador

function RegisterPaymentView() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const toast = useToast();

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [searchTerm, setSearchTerm] = useState("");
  const [foundUsers, setFoundUsers] = useState<UserDetail[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [pendingInvoices, setPendingInvoices] = useState<Invoice[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  const [paymentMethod, setPaymentMethod] = useState("Efectivo");
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().split("T")[0]
  ); // Fecha de hoy por defecto
  const [receiptFile, setReceiptFile] = useState<File | null>(null);

  // Efecto para buscar usuarios cuando el término de búsqueda cambia
  useEffect(() => {
    if (searchTerm.length < 3) {
      setFoundUsers([]);
      return;
    }
    // Aquí iría la lógica para buscar usuarios (usando un endpoint que crearemos después si es necesario)
    // Por ahora, lo simularemos o asumiremos que el admin conoce al usuario.
  }, [searchTerm]);

  // Efecto para buscar facturas pendientes cuando se selecciona un usuario
  useEffect(() => {
    if (selectedUser && token) {
      setIsLoading(true);
      getPendingInvoicesByUserId(selectedUser.id, token)
        .then((invoices) => setPendingInvoices(invoices))
        .catch(() =>
          toast({
            title: "Error",
            description: "No se pudieron cargar las facturas pendientes.",
            status: "error",
          })
        )
        .finally(() => setIsLoading(false));
    }
  }, [selectedUser, token, toast]);

  const handleSelectInvoice = (invoiceId: string) => {
    const invoice = pendingInvoices.find((inv) => inv.id === Number(invoiceId));
    setSelectedInvoice(invoice || null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setReceiptFile(e.target.files[0]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedInvoice) {
      toast({
        title: "Error",
        description: "Debe seleccionar una factura.",
        status: "error",
      });
      return;
    }

    setIsSaving(true);
    const formData = new FormData();
    formData.append("invoice_id", String(selectedInvoice.id));
    formData.append("amount", String(selectedInvoice.amount)); // Usamos el monto de la factura
    formData.append("payment_date", paymentDate);
    formData.append("payment_method", paymentMethod);
    if (receiptFile) {
      formData.append("receipt_file", receiptFile);
    }

    try {
      await registerManualPayment(formData, token);
      toast({ title: "Pago Registrado", status: "success" });
      navigate("/admin/payments");
    } catch (err: any) {
      const errorDescription =
        err.response?.data?.detail || "Ocurrió un error.";
      toast({
        title: "Error al registrar el pago",
        description: errorDescription,
        status: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Box p={{ base: 4, md: 8 }} bg="gray.800" color="white" minH="100vh">
      <VStack spacing={6} align="stretch" maxW="800px" mx="auto">
        <HStack justify="space-between">
          <Heading as="h1" size="xl">
            Registrar Pago Manual
          </Heading>
          <Button onClick={() => navigate("/admin/payments")}>Volver</Button>
        </HStack>
        <Card bg="gray.700" color="white">
          <CardHeader>
            <Heading size="md">Datos del Pago</Heading>
          </CardHeader>
          <CardBody>
            {/* Aquí podríamos poner el buscador de clientes en el futuro */}
            {/* Por ahora seleccionamos una factura pendiente directamente */}
            <Box as="form" onSubmit={handleSave}>
              <VStack spacing={4}>
                {/* Selector de Facturas (simplificado por ahora) */}
                {/* Lo ideal sería buscar un cliente y luego mostrar sus facturas */}
                <FormControl isRequired>
                  <FormLabel>Factura Pendiente a Pagar</FormLabel>
                  <Select
                    placeholder="Seleccione una factura..."
                    onChange={(e) => handleSelectInvoice(e.target.value)}
                  >
                    {/* Aquí necesitaríamos una lista de todas las facturas pendientes */}
                    {/* Esto es una simplificación y lo mejoraremos */}
                  </Select>
                </FormControl>

                {selectedInvoice && (
                  <>
                    <SimpleGrid columns={2} spacing={4} w="100%">
                      <FormControl>
                        <FormLabel>Monto a Pagar</FormLabel>
                        <Input
                          value={`$${selectedInvoice.amount.toFixed(2)}`}
                          isReadOnly
                          bg="gray.600"
                        />
                      </FormControl>
                      <FormControl isRequired>
                        <FormLabel>Fecha de Pago</FormLabel>
                        <Input
                          type="date"
                          value={paymentDate}
                          onChange={(e) => setPaymentDate(e.target.value)}
                        />
                      </FormControl>
                    </SimpleGrid>

                    <FormControl isRequired>
                      <FormLabel>Método de Pago</FormLabel>
                      <Select
                        value={paymentMethod}
                        onChange={(e) => setPaymentMethod(e.target.value)}
                      >
                        <option
                          value="Efectivo"
                          style={{ backgroundColor: "#2D3748" }}
                        >
                          Efectivo
                        </option>
                        <option
                          value="Transferencia"
                          style={{ backgroundColor: "#2D3748" }}
                        >
                          Transferencia
                        </option>
                      </Select>
                    </FormControl>

                    {paymentMethod === "Transferencia" && (
                      <FormControl isRequired>
                        <FormLabel>Comprobante de Transferencia</FormLabel>
                        <Input
                          type="file"
                          onChange={handleFileChange}
                          p={1}
                          accept=".pdf,.png,.jpg,.jpeg"
                        />
                      </FormControl>
                    )}

                    <HStack w="100%" pt={4}>
                      <Button
                        onClick={() => navigate("/admin/payments")}
                        flex={1}
                      >
                        Cancelar
                      </Button>
                      <Button
                        colorScheme="teal"
                        type="submit"
                        flex={1}
                        isLoading={isSaving}
                      >
                        Registrar Pago
                      </Button>
                    </HStack>
                  </>
                )}
              </VStack>
            </Box>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
}

export default RegisterPaymentView;
