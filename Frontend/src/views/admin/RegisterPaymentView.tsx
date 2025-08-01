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
} from "@chakra-ui/react";
import AsyncSelect from "react-select/async";
import { useAuth } from "../../context/AuthContext";
import {
  UserDetail,
  Invoice,
  getPendingInvoicesByUserId,
  registerManualPayment,
  searchUsers,
} from "../../services/adminService";

// --- Componente para la "Tarjeta" de Cliente Seleccionado ---
const SelectedClientCard = ({ user }: { user: UserDetail }) => (
  <Box p={4} bg="gray.600" borderRadius="md" w="100%" mt={4}>
    <Text fontWeight="bold" fontSize="lg">
      {user.firstname} {user.lastname}
    </Text>
    <Text fontSize="sm" color="gray.300">
      DNI: {user.dni}
    </Text>
    <Text fontSize="sm" color="gray.300">
      {user.address || "Sin dirección"}, {user.city || "Sin ciudad"}
    </Text>
  </Box>
);

function RegisterPaymentView() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const toast = useToast();

  const [isLoadingInvoices, setIsLoadingInvoices] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [pendingInvoices, setPendingInvoices] = useState<Invoice[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [paymentMethod, setPaymentMethod] = useState("Efectivo");
  const [paymentDate, setPaymentDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [amount, setAmount] = useState(0);

  // Función que alimenta al buscador con sugerencias de clientes
  const loadUserOptions = (
    inputValue: string,
    callback: (options: UserDetail[]) => void
  ) => {
    if (!token || inputValue.length < 3) {
      callback([]);
      return;
    }
    searchUsers(inputValue, token)
      .then((users) => callback(users))
      .catch(() => callback([]));
  };

  // Efecto que se dispara al seleccionar un cliente para buscar sus facturas
  useEffect(() => {
    if (selectedUser && token) {
      setIsLoadingInvoices(true);
      setPendingInvoices([]);
      setSelectedInvoice(null);
      getPendingInvoicesByUserId(selectedUser.id, token)
        .then((invoices) => {
          setPendingInvoices(invoices);
          if (invoices.length === 0) {
            toast({
              title: "Sin Deudas",
              description: "Este cliente no tiene facturas pendientes.",
              status: "info",
              isClosable: true,
            });
          }
        })
        .catch(() =>
          toast({
            title: "Error",
            description: "No se pudieron cargar las facturas.",
            status: "error",
            isClosable: true,
          })
        )
        .finally(() => setIsLoadingInvoices(false));
    }
  }, [selectedUser, token, toast]);

  // Efecto para autocompletar el monto al seleccionar una factura
  useEffect(() => {
    if (selectedInvoice) {
      setAmount(selectedInvoice.total_amount);
    } else {
      setAmount(0);
    }
  }, [selectedInvoice]);

  const handleSelectInvoice = (invoiceId: string) => {
    const invoice = pendingInvoices.find((inv) => inv.id === Number(invoiceId));
    setSelectedInvoice(invoice || null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setReceiptFile(e.target.files[0]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedInvoice) {
      toast({
        title: "Datos incompletos",
        description: "Debes seleccionar un cliente y una factura.",
        status: "error",
      });
      return;
    }
    setIsSaving(true);
    const formData = new FormData();
    formData.append("invoice_id", String(selectedInvoice.id));
    formData.append("amount", String(amount));
    formData.append("payment_date", paymentDate);
    formData.append("payment_method", paymentMethod);
    if (receiptFile && paymentMethod === "Transferencia") {
      formData.append("receipt_file", receiptFile);
    }
    try {
      await registerManualPayment(formData, token);
      toast({
        title: "Pago Registrado",
        description: "El pago se ha guardado exitosamente.",
        status: "success",
      });
      navigate("/admin/payments");
    } catch (err: any) {
      const errorDescription =
        err.response?.data?.detail || "Ocurrió un error.";
      toast({
        title: "Error al registrar",
        description: errorDescription,
        status: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Estilos para que el buscador combine con el tema oscuro de Chakra UI
  const selectStyles = {
    control: (base: any) => ({
      ...base,
      backgroundColor: "#2D3748",
      border: "1px solid #4A5568",
      color: "white",
    }),
    menu: (base: any) => ({ ...base, backgroundColor: "#2D3748" }),
    option: (base: any, state: { isFocused: any }) => ({
      ...base,
      backgroundColor: state.isFocused ? "#4A5568" : "#2D3748",
      color: "white",
    }),
    singleValue: (base: any) => ({ ...base, color: "white" }),
    input: (base: any) => ({ ...base, color: "white" }),
  };

  return (
    <Box p={{ base: 4, md: 8 }} bg="gray.800" color="white" minH="100vh">
      <VStack spacing={6} align="stretch" maxW="800px" mx="auto">
        <HStack justify="space-between">
          <Heading as="h1" size="xl">
            Registrar Pago Manual
          </Heading>
          <Button onClick={() => navigate("/admin/payments")}>
            Volver al Historial
          </Button>
        </HStack>
        <Card bg="gray.700" color="white">
          <CardHeader>
            <Heading size="md">Completa los Datos del Pago</Heading>
          </CardHeader>
          <CardBody as="form" onSubmit={handleSave}>
            <VStack spacing={6}>
              <FormControl isRequired>
                <FormLabel fontWeight="bold" mb={2}>
                  Paso 1: Buscar y Seleccionar Cliente
                </FormLabel>
                <AsyncSelect
                  styles={selectStyles}
                  loadOptions={loadUserOptions}
                  onChange={(option) => setSelectedUser(option as UserDetail)}
                  getOptionLabel={(user) =>
                    `${user.firstname} ${user.lastname} (DNI: ${user.dni})`
                  }
                  getOptionValue={(user) => String(user.id)}
                  placeholder="Escribe 3+ letras del nombre o DNI..."
                  noOptionsMessage={() => "No se encontraron clientes"}
                  loadingMessage={() => "Buscando..."}
                />
              </FormControl>

              {selectedUser && <SelectedClientCard user={selectedUser} />}

              {isLoadingInvoices && <Spinner my={4} />}

              {selectedUser && !isLoadingInvoices && (
                <VStack w="100%" spacing={4}>
                  <FormControl
                    isRequired
                    isDisabled={pendingInvoices.length === 0}
                  >
                    <FormLabel fontWeight="bold">
                      Paso 2: Seleccionar Factura Pendiente
                    </FormLabel>
                    <Select
                      placeholder={
                        pendingInvoices.length === 0
                          ? "Este cliente no tiene deudas"
                          : "Elige una factura..."
                      }
                      onChange={(e) => handleSelectInvoice(e.target.value)}
                      bg="gray.600"
                    >
                      {pendingInvoices.map((inv) => (
                        <option
                          key={inv.id}
                          value={inv.id}
                          style={{ backgroundColor: "#2D3748" }}
                        >
                          Factura #{inv.id} - ${inv.total_amount.toFixed(2)}{" "}
                          (Vence: {new Date(inv.due_date).toLocaleDateString()})
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  {selectedInvoice && (
                    <VStack
                      w="100%"
                      spacing={4}
                      pt={4}
                      borderTop="1px solid"
                      borderColor="gray.600"
                    >
                      <FormLabel fontWeight="bold" alignSelf="flex-start">
                        Paso 3: Detallar el Pago
                      </FormLabel>
                      <SimpleGrid columns={2} spacing={4} w="100%">
                        <FormControl isRequired>
                          <FormLabel>Monto del Pago</FormLabel>
                          <Input
                            type="number"
                            step="0.01"
                            value={amount}
                            onChange={(e) => setAmount(Number(e.target.value))}
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
                          bg="gray.600"
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
                          <FormLabel>Comprobante</FormLabel>
                          <Input
                            type="file"
                            onChange={handleFileChange}
                            p={1}
                            accept=".pdf,.png,.jpg,.jpeg"
                            sx={{ "::file-selector-button": { mr: 2 } }}
                          />
                        </FormControl>
                      )}
                      <HStack w="100%" pt={4}>
                        <Button
                          variant="ghost"
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
                    </VStack>
                  )}
                </VStack>
              )}
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  );
}

export default RegisterPaymentView;
