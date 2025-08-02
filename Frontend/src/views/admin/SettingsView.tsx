// Frontend/src/views/admin/SettingsView.tsx
import { useState, useEffect } from "react";
import {
  Box,
  Heading,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  Button,
  useToast,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  FormControl,
  FormLabel,
  Input,
  Switch,
  HStack,
  InputGroup,
  InputLeftAddon,
} from "@chakra-ui/react";
import { useAuth } from "../../context/AuthContext";
import {
  getSettings,
  updateSettings,
  CompanySettings,
} from "../../services/adminService";

const initialSettings: CompanySettings = {
  business_name: "",
  business_cuit: "",
  business_address: "",
  business_city: "",
  business_phone: "",
  payment_window_days: 0,
  late_fee_amount: 0,
  auto_invoicing_enabled: false,
  days_for_suspension: 0,
};

function SettingsView() {
  const [settings, setSettings] = useState<CompanySettings>(initialSettings);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();
  const toast = useToast();

  useEffect(() => {
    if (token) {
      getSettings(token)
        .then(setSettings)
        .catch(() => setError("No se pudieron cargar las configuraciones."))
        .finally(() => setIsLoading(false));
    }
  }, [token]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setSettings((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? checked
          : type === "number"
          ? parseFloat(value) || 0
          : value,
    }));
  };

  const handleSave = async () => {
    if (!token) return;
    setIsSaving(true);
    try {
      await updateSettings(settings, token);
      toast({ title: "Configuración Guardada", status: "success" });
    } catch (err: any) {
      toast({
        title: "Error al guardar",
        description: err.response?.data?.detail,
        status: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading)
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <Spinner size="xl" />
      </Box>
    );
  if (error)
    return (
      <Box p={8}>
        <Alert status="error">
          <AlertIcon />
          {error}
        </Alert>
      </Box>
    );

  return (
    <Box p={{ base: 4, md: 8 }} bg="gray.800" color="white" minH="100vh">
      <VStack spacing={6} align="stretch" maxW="900px" mx="auto">
        <HStack justify="space-between">
          <Heading as="h1" size="xl">
            Configuraciones
          </Heading>
          <Button colorScheme="teal" onClick={handleSave} isLoading={isSaving}>
            Guardar Cambios
          </Button>
        </HStack>

        <Accordion allowToggle defaultIndex={[0]}>
          <AccordionItem bg="gray.700" borderRadius="md" mb={4}>
            <h2>
              <AccordionButton _expanded={{ bg: "teal.500" }}>
                <Box as="span" flex="1" textAlign="left" fontWeight="bold">
                  Datos de la Empresa
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4} pt={4}>
              <VStack spacing={4}>
                <FormControl>
                  <FormLabel>Nombre de la Empresa</FormLabel>
                  <Input
                    name="business_name"
                    value={settings.business_name}
                    onChange={handleChange}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>CUIT</FormLabel>
                  <Input
                    name="business_cuit"
                    value={settings.business_cuit}
                    onChange={handleChange}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Dirección Fiscal</FormLabel>
                  <Input
                    name="business_address"
                    value={settings.business_address}
                    onChange={handleChange}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Ciudad</FormLabel>
                  <Input
                    name="business_city"
                    value={settings.business_city}
                    onChange={handleChange}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Teléfono</FormLabel>
                  <Input
                    name="business_phone"
                    value={settings.business_phone}
                    onChange={handleChange}
                  />
                </FormControl>
              </VStack>
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem bg="gray.700" borderRadius="md" mb={4}>
            <h2>
              <AccordionButton _expanded={{ bg: "teal.500" }}>
                <Box as="span" flex="1" textAlign="left" fontWeight="bold">
                  Reglas de Facturación
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4} pt={4}>
              <VStack spacing={4}>
                <FormControl>
                  <FormLabel>Días de Plazo para Pagar</FormLabel>
                  <InputGroup>
                    <Input
                      name="payment_window_days"
                      type="number"
                      value={settings.payment_window_days}
                      onChange={handleChange}
                    />
                    <InputLeftAddon children="días" />
                  </InputGroup>
                </FormControl>
                <FormControl>
                  <FormLabel>Monto por Mora</FormLabel>
                  <InputGroup>
                    <InputLeftAddon children="$" />
                    <Input
                      name="late_fee_amount"
                      type="number"
                      value={settings.late_fee_amount}
                      onChange={handleChange}
                    />
                  </InputGroup>
                </FormControl>
              </VStack>
            </AccordionPanel>
          </AccordionItem>

          <AccordionItem bg="gray.700" borderRadius="md" mb={4}>
            <h2>
              <AccordionButton _expanded={{ bg: "teal.500" }}>
                <Box as="span" flex="1" textAlign="left" fontWeight="bold">
                  Automatización
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4} pt={4}>
              <VStack spacing={4}>
                <FormControl
                  display="flex"
                  alignItems="center"
                  justifyContent="space-between"
                >
                  <FormLabel htmlFor="auto_invoicing_enabled" mb="0">
                    Facturación Automática
                  </FormLabel>
                  <Switch
                    id="auto_invoicing_enabled"
                    name="auto_invoicing_enabled"
                    isChecked={settings.auto_invoicing_enabled}
                    onChange={handleChange}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Días para Suspensión por Deuda</FormLabel>
                  <InputGroup>
                    <Input
                      name="days_for_suspension"
                      type="number"
                      value={settings.days_for_suspension}
                      onChange={handleChange}
                    />
                    <InputLeftAddon children="días" />
                  </InputGroup>
                </FormControl>
              </VStack>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>
      </VStack>
    </Box>
  );
}

export default SettingsView;
