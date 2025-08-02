// Frontend/src/views/admin/ClientEditView.tsx
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
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
  Spinner,
  Alert,
  AlertIcon,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Text,
  // --- 1. IMPORTACIONES PARA EL ACORDEÓN ---
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from "@chakra-ui/react";
import { useAuth } from "../../context/AuthContext";
import {
  getUserById,
  updateUserDetails,
  deleteUser,
  UserDetail,
  Subscription,
  getUserSubscriptions,
} from "../../services/adminService";
import { getAllPlans } from "../../services/planService";
import { Plan } from "./PlanManagement";
import { SubscriptionPanel } from "../../components/admin/subscriptions/SubscriptionPanel";

function ClientEditView() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [user, setUser] = useState<UserDetail | null>(null);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);

  const fetchData = async () => {
    if (userId && token) {
      setIsLoading(true);
      try {
        const [userData, subsData, plansData] = await Promise.all([
          getUserById(Number(userId), token),
          getUserSubscriptions(Number(userId), token),
          getAllPlans(),
        ]);
        setUser(userData);
        setSubscriptions(subsData);
        setPlans(plansData.items);
      } catch (err: any) {
        setError(
          err.response?.data?.detail ||
            "No se pudo cargar toda la información del cliente."
        );
      } finally {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchData();
  }, [userId, token]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setUser((prev) => (prev ? { ...prev, [name]: value } : null));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !user) return;
    setIsSaving(true);
    try {
      const { id, firstname, lastname, address, barrio, city, phone, phone2 } =
        user;
      await updateUserDetails(
        id,
        { firstname, lastname, address, barrio, city, phone, phone2 },
        token
      );
      toast({ title: "Cliente Actualizado", status: "success" });
      navigate("/admin/clients");
    } catch (err: any) {
      toast({
        title: "Error al actualizar",
        description: err.response?.data?.detail,
        status: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!token || !user) return;
    setIsDeleting(true);
    try {
      await deleteUser(user.id, token);
      toast({ title: "Cliente Eliminado", status: "warning" });
      navigate("/admin/clients");
    } catch (err: any) {
      toast({
        title: "Error al eliminar",
        description: err.response?.data?.detail,
        status: "error",
      });
    } finally {
      setIsDeleting(false);
      onClose();
    }
  };

  if (isLoading)
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="80vh"
      >
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
    <>
      <Box p={{ base: 4, md: 8 }} bg="gray.800" color="white" minH="100vh">
        <VStack spacing={6} align="stretch" maxW="900px" mx="auto">
          <HStack justify="space-between">
            <Heading as="h1" size="xl">
              Editar Cliente
            </Heading>
            <Button onClick={() => navigate("/admin/clients")}>Volver</Button>
          </HStack>

          {user && (
            // --- 2. ESTRUCTURA VISUAL CON ACORDEÓN ---
            <Accordion
              allowToggle
              defaultIndex={[0]}
              bg="gray.700"
              borderRadius="md"
            >
              {/* SECCIÓN 1: DATOS DEL CLIENTE */}
              <AccordionItem border="none">
                <h2>
                  <AccordionButton
                    _expanded={{ bg: "teal.500", color: "white" }}
                  >
                    <Box as="span" flex="1" textAlign="left" fontWeight="bold">
                      Datos Personales de @{user.username}
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel pb={4}>
                  <Box as="form" onSubmit={handleSave}>
                    <VStack spacing={4} pt={4}>
                      <HStack w="100%">
                        <FormControl isRequired>
                          <FormLabel>Nombre</FormLabel>
                          <Input
                            name="firstname"
                            value={user.firstname}
                            onChange={handleInputChange}
                          />
                        </FormControl>
                        <FormControl isRequired>
                          <FormLabel>Apellido</FormLabel>
                          <Input
                            name="lastname"
                            value={user.lastname}
                            onChange={handleInputChange}
                          />
                        </FormControl>
                      </HStack>
                      <FormControl>
                        <FormLabel>DNI</FormLabel>
                        <Input value={user.dni} isReadOnly bg="gray.600" />
                      </FormControl>
                      <FormControl>
                        <FormLabel>Email</FormLabel>
                        <Input
                          type="email"
                          readOnly
                          value={user.email}
                          bg="gray.600"
                        />
                      </FormControl>
                      <FormControl>
                        <FormLabel>Dirección</FormLabel>
                        <Input
                          name="address"
                          value={user.address || ""}
                          onChange={handleInputChange}
                        />
                      </FormControl>
                      <HStack w="100%">
                        <FormControl>
                          <FormLabel>Barrio</FormLabel>
                          <Input
                            name="barrio"
                            value={user.barrio || ""}
                            onChange={handleInputChange}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>Ciudad</FormLabel>
                          <Input
                            name="city"
                            value={user.city || ""}
                            onChange={handleInputChange}
                          />
                        </FormControl>
                      </HStack>
                      <HStack w="100%">
                        <FormControl>
                          <FormLabel>Teléfono</FormLabel>
                          <Input
                            name="phone"
                            value={user.phone || ""}
                            onChange={handleInputChange}
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel>Teléfono 2</FormLabel>
                          <Input
                            name="phone2"
                            value={user.phone2 || ""}
                            onChange={handleInputChange}
                          />
                        </FormControl>
                      </HStack>
                      <HStack w="100%" pt={4}>
                        <Button
                          colorScheme="red"
                          variant="outline"
                          onClick={onOpen}
                        >
                          Eliminar Cliente
                        </Button>
                        <Button
                          colorScheme="teal"
                          type="submit"
                          flex={1}
                          isLoading={isSaving}
                        >
                          Guardar Cambios
                        </Button>
                      </HStack>
                    </VStack>
                  </Box>
                </AccordionPanel>
              </AccordionItem>

              {/* SECCIÓN 2: GESTIÓN DE SUSCRIPCIÓN */}
              <AccordionItem border="none">
                <h2>
                  <AccordionButton
                    _expanded={{ bg: "teal.500", color: "white" }}
                  >
                    <Box as="span" flex="1" textAlign="left" fontWeight="bold">
                      Gestión de Suscripción
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                </h2>
                <AccordionPanel pb={4}>
                  <SubscriptionPanel
                    userId={user.id}
                    subscriptions={subscriptions}
                    plans={plans}
                    onSubscriptionUpdate={fetchData}
                  />
                </AccordionPanel>
              </AccordionItem>
            </Accordion>
          )}
        </VStack>
      </Box>

      {/* Modal de Confirmación para Eliminar */}
      <Modal isOpen={isOpen} onClose={onClose} isCentered>
        <ModalOverlay />
        <ModalContent bg="gray.700" color="white">
          <ModalHeader>Confirmar Eliminación</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              ¿Estás seguro? Se eliminará al cliente{" "}
              <strong>
                {user?.firstname} {user?.lastname}
              </strong>
              .
            </Text>
            <Text mt={2} color="red.300">
              Esta acción no se puede deshacer.
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancelar
            </Button>
            <Button
              colorScheme="red"
              isLoading={isDeleting}
              onClick={handleDelete}
            >
              Sí, Eliminar
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}

export default ClientEditView;
