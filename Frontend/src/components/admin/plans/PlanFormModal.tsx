// src/components/admin/plans/PlanFormModal.tsx
import { useState, useEffect } from "react";
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  useToast,
  InputGroup,
  InputLeftAddon,
  Box,
} from "@chakra-ui/react";
import { useAuth } from "../../../context/AuthContext";
import { Plan } from "../../../views/admin/PlanManagement";
// Importaremos las funciones del servicio que crearemos en el siguiente paso
import { createPlan, updatePlan } from "../../../services/planService";

interface PlanFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan: Plan | null; // Si es 'null', es para crear. Si tiene datos, es para editar.
}

export const PlanFormModal = ({
  isOpen,
  onClose,
  plan,
}: PlanFormModalProps) => {
  const [formData, setFormData] = useState({
    name: "",
    speed_mbps: "",
    price: "",
  });
  const [isSaving, setIsSaving] = useState(false);
  const toast = useToast();
  const { token } = useAuth();

  // Este efecto llena el formulario con los datos del plan cuando se abre para editar
  useEffect(() => {
    if (plan) {
      setFormData({
        name: plan.name,
        speed_mbps: String(plan.speed_mbps),
        price: String(plan.price),
      });
    } else {
      // Si es para crear, reseteamos el formulario
      setFormData({ name: "", speed_mbps: "", price: "" });
    }
  }, [plan, isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsSaving(true);
    const planData = {
      name: formData.name,
      speed_mbps: Number(formData.speed_mbps),
      price: Number(formData.price),
    };

    try {
      if (plan) {
        // Modo Edición
        await updatePlan(plan.id, planData, token);
        toast({ title: "Plan Actualizado", status: "success" });
      } else {
        // Modo Creación
        await createPlan(planData, token);
        toast({ title: "Plan Creado", status: "success" });
      }
      onClose(); // Cierra el modal y refresca la lista de planes
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Ocurrió un error.";
      toast({
        title: "Error al guardar",
        description: errorMsg,
        status: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered>
      <ModalOverlay />
      <ModalContent bg="gray.700" color="white">
        <ModalHeader>{plan ? "Editar Plan" : "Crear Nuevo Plan"}</ModalHeader>
        <ModalCloseButton />
        <Box as="form" onSubmit={handleSubmit}>
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Nombre del Plan</FormLabel>
                <Input
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Ej: Fibra 100MB"
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Velocidad</FormLabel>
                <InputGroup>
                  <Input
                    name="speed_mbps"
                    type="number"
                    value={formData.speed_mbps}
                    onChange={handleInputChange}
                    placeholder="Ej: 100"
                  />
                  <InputLeftAddon bg="gray.600" children="Mbps" />
                </InputGroup>
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Precio</FormLabel>
                <InputGroup>
                  <InputLeftAddon bg="gray.600" children="$" />
                  <Input
                    name="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={handleInputChange}
                    placeholder="Ej: 6000.00"
                  />
                </InputGroup>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancelar
            </Button>
            <Button colorScheme="teal" type="submit" isLoading={isSaving}>
              Guardar
            </Button>
          </ModalFooter>
        </Box>
      </ModalContent>
    </Modal>
  );
};
