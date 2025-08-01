// src/views/admin/PlanManagement.tsx
import { useState, useEffect } from "react";
import {
  Box,
  Heading,
  VStack,
  Spinner,
  Alert,
  AlertIcon,
  HStack,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  IconButton,
  useDisclosure,
  useToast,
  Text,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
} from "@chakra-ui/react";
import { EditIcon, DeleteIcon } from "@chakra-ui/icons";
import { useAuth } from "../../context/AuthContext";
import { getAllPlans, deletePlan } from "../../services/planService";
import { PlanFormModal } from "../../components/admin/plans/PlanFormModal";

// Definimos el tipo de dato para un Plan
export interface Plan {
  id: number;
  name: string;
  speed_mbps: number;
  price: number;
}

function PlanManagement() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();
  const toast = useToast();

  // Un controlador para el modal de Crear/Editar
  const {
    isOpen: isFormOpen,
    onOpen: onFormOpen,
    onClose: onFormClose,
  } = useDisclosure();
  // Un controlador para el modal de Eliminar
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchPlans = () => {
    if (!token) return;
    setIsLoading(true);
    getAllPlans()
      .then((data) => setPlans(data.items))
      .catch(() => setError("No se pudieron cargar los planes."))
      .finally(() => setIsLoading(false));
  };

  useEffect(fetchPlans, [token]);

  const handleOpenFormModal = (plan: Plan | null) => {
    setSelectedPlan(plan);
    onFormOpen();
  };

  const handleOpenDeleteModal = (plan: Plan) => {
    setSelectedPlan(plan);
    onDeleteOpen();
  };

  const handleCloseModals = () => {
    setSelectedPlan(null);
    onFormClose();
    onDeleteClose();
    fetchPlans();
  };

  const handleDelete = async () => {
    if (!token || !selectedPlan) return;

    setIsDeleting(true);
    try {
      await deletePlan(selectedPlan.id, token);
      toast({ title: "Plan Eliminado", status: "success" });
      handleCloseModals();
    } catch (err: any) {
      const errorMsg =
        err.response?.data?.detail || "Error al eliminar el plan.";
      toast({ title: "Error", description: errorMsg, status: "error" });
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <Spinner size="xl" />
      </Box>
    );
  }

  return (
    <>
      <Box
        p={{ base: 4, md: 8 }}
        bg="gray.800"
        color="white"
        minH="calc(100vh - 4rem)"
      >
        <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
          <HStack justify="space-between">
            <Heading as="h1" size="xl">
              Gestión de Planes
            </Heading>
            <Button
              colorScheme="teal"
              onClick={() => handleOpenFormModal(null)}
            >
              Crear Nuevo Plan
            </Button>
          </HStack>

          {error && (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              {error}
            </Alert>
          )}

          <TableContainer bg="gray.700" borderRadius="md">
            <Table variant="simple" color="white">
              <Thead>
                <Tr>
                  <Th color="gray.400" borderBottomColor="gray.600">
                    Nombre del Plan
                  </Th>
                  <Th color="gray.400" isNumeric borderBottomColor="gray.600">
                    Velocidad (Mbps)
                  </Th>
                  <Th color="gray.400" isNumeric borderBottomColor="gray.600">
                    Precio
                  </Th>
                  <Th
                    color="gray.400"
                    textAlign="center"
                    borderBottomColor="gray.600"
                  >
                    Acciones
                  </Th>
                </Tr>
              </Thead>
              <Tbody>
                {plans.map((plan) => (
                  <Tr key={plan.id} _hover={{ bg: "gray.600" }}>
                    <Td fontWeight="medium">{plan.name}</Td>
                    <Td isNumeric>{plan.speed_mbps}</Td>
                    <Td isNumeric>${plan.price.toLocaleString("es-AR")}</Td>
                    <Td textAlign="center">
                      <IconButton
                        aria-label="Editar Plan"
                        icon={<EditIcon />}
                        variant="ghost"
                        onClick={() => handleOpenFormModal(plan)}
                        mr={2}
                      />
                      <IconButton
                        aria-label="Eliminar Plan"
                        icon={<DeleteIcon />}
                        variant="ghost"
                        colorScheme="red"
                        onClick={() => handleOpenDeleteModal(plan)}
                      />
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        </VStack>
      </Box>

      {/* Modal para Crear/Editar Plan */}
      <PlanFormModal
        isOpen={isFormOpen}
        onClose={handleCloseModals}
        plan={selectedPlan}
      />

      {/* Modal para Confirmar Eliminación */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose} isCentered>
        <ModalOverlay />
        <ModalContent bg="gray.700" color="white">
          <ModalHeader>Confirmar Eliminación</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              ¿Estás seguro de que deseas eliminar el plan{" "}
              <strong>"{selectedPlan?.name}"</strong>?
            </Text>
            <Text mt={2} color="red.300" fontSize="sm">
              Esta acción no se puede deshacer.
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onDeleteClose}>
              Cancelar
            </Button>
            <Button
              colorScheme="red"
              isLoading={isDeleting}
              onClick={handleDelete}
            >
              Eliminar
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}

export default PlanManagement;
