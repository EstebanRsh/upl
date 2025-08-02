// Frontend/src/components/admin/subscriptions/SubscriptionPanel.tsx
import { useState } from "react";
import {
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Select,
  FormControl,
  FormLabel,
  useToast,
} from "@chakra-ui/react";
import { useAuth } from "../../../context/AuthContext";
import {
  assignPlanToUser,
  updateSubscriptionStatus,
  Subscription,
} from "../../../services/adminService";
import { Plan } from "../../../views/admin/PlanManagement";

// --- Componente auxiliar para mostrar filas de información ---
const InfoRow = ({ label, value }: { label: string; value: string | null }) => (
  <HStack justify="space-between" w="100%">
    <Text color="gray.400">{label}:</Text>
    <Text fontWeight="medium">{value || "No especificado"}</Text>
  </HStack>
);

// --- Props que el componente recibirá ---
interface SubscriptionPanelProps {
  userId: number;
  subscriptions: Subscription[];
  plans: Plan[];
  onSubscriptionUpdate: () => void; // Función para recargar los datos del componente padre
}

export const SubscriptionPanel = ({
  userId,
  subscriptions,
  plans,
  onSubscriptionUpdate,
}: SubscriptionPanelProps) => {
  const { token } = useAuth();
  const toast = useToast();
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(
    plans[0]?.id || null
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Buscamos la primera suscripción activa
  const activeSubscription = subscriptions.find((s) => s.status === "active");

  const handleAssignPlan = async () => {
    if (!selectedPlanId || !token) return;
    setIsSubmitting(true);
    try {
      await assignPlanToUser(userId, selectedPlanId, token);
      toast({ title: "Plan Asignado", status: "success", isClosable: true });
      onSubscriptionUpdate(); // Avisa al padre que actualice los datos
    } catch (err: any) {
      toast({
        title: "Error al asignar",
        description: err.response?.data?.detail || "Ocurrió un error.",
        status: "error",
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusChange = async (
    subscriptionId: number,
    status: "active" | "suspended" | "cancelled"
  ) => {
    if (!token) return;
    setIsSubmitting(true);
    try {
      await updateSubscriptionStatus(subscriptionId, status, token);
      toast({ title: "Estado Actualizado", status: "info", isClosable: true });
      onSubscriptionUpdate(); // Avisa al padre que actualice los datos
    } catch (err: any) {
      toast({
        title: "Error al actualizar",
        description: err.response?.data?.detail || "Ocurrió un error.",
        status: "error",
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (activeSubscription) {
    const { plan, status, id: subId } = activeSubscription;
    return (
      <VStack spacing={4} align="stretch">
        <InfoRow label="Plan Contratado" value={plan.name} />
        <InfoRow label="Precio Mensual" value={`$${plan.price.toFixed(2)}`} />
        <HStack justify="space-between">
          <Text color="gray.400">Estado:</Text>
          <Badge colorScheme={status === "active" ? "green" : "yellow"}>
            {status.toUpperCase()}
          </Badge>
        </HStack>
        <HStack pt={4}>
          <Button
            size="sm"
            onClick={() => handleStatusChange(subId, "suspended")}
            isDisabled={status === "suspended" || isSubmitting}
            isLoading={isSubmitting}
          >
            Suspender
          </Button>
          <Button
            size="sm"
            onClick={() => handleStatusChange(subId, "active")}
            isDisabled={status === "active" || isSubmitting}
            isLoading={isSubmitting}
          >
            Reactivar
          </Button>
          <Button
            size="sm"
            colorScheme="red"
            variant="outline"
            onClick={() => handleStatusChange(subId, "cancelled")}
            isLoading={isSubmitting}
          >
            Cancelar
          </Button>
        </HStack>
      </VStack>
    );
  }

  return (
    <VStack spacing={4} align="stretch">
      <Text color="yellow.400">Este cliente no tiene un plan activo.</Text>
      <FormControl>
        <FormLabel>Seleccionar Plan</FormLabel>
        <Select
          bg="gray.600"
          value={selectedPlanId || ""}
          onChange={(e) => setSelectedPlanId(Number(e.target.value))}
        >
          {plans.length > 0 ? (
            plans.map((p) => (
              <option
                key={p.id}
                value={p.id}
                style={{ backgroundColor: "#2D3748" }}
              >
                {p.name} (${p.price})
              </option>
            ))
          ) : (
            <option style={{ backgroundColor: "#2D3748" }} disabled>
              No hay planes disponibles
            </option>
          )}
        </Select>
      </FormControl>
      <Button
        colorScheme="teal"
        onClick={handleAssignPlan}
        isLoading={isSubmitting}
        isDisabled={!selectedPlanId || plans.length === 0}
      >
        Asignar Nuevo Plan
      </Button>
    </VStack>
  );
};
