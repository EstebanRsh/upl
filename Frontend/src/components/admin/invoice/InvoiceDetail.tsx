// src/components/admin/invoice/InvoiceDetail.tsx
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  Button,
} from "@chakra-ui/react";
import { InvoiceAdminOut } from "../../../models/Invoice";

const InfoRow = ({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) => (
  <HStack justify="space-between" w="100%">
    <Text color="gray.400">{label}:</Text>
    <Text fontWeight="bold">{value}</Text>
  </HStack>
);
const StatusBadge = ({ status }: { status: string }) => {
  const config = {
    paid: { s: "green", t: "Pagada" },
    overdue: { s: "red", t: "Vencida" },
    in_review: { s: "cyan", t: "En Verificación" },
    pending: { s: "yellow", t: "Pendiente" },
  }[status as "paid" | "overdue" | "in_review" | "pending"] || {
    s: "gray",
    t: "Desconocido",
  };
  return (
    <Badge fontSize="md" colorScheme={config.s}>
      {config.t}
    </Badge>
  );
};

// --- INICIO DE LA CORRECCIÓN ---
interface InvoiceDetailProps {
  invoice: InvoiceAdminOut | null;
  isLoading: boolean;
  error: string | null;
  isUpdating: boolean; // Propiedad para saber si se está actualizando
  onUpdateStatus: (newStatus: string) => void; // Propiedad para la función de callback
}
// --- FIN DE LA CORRECCIÓN ---

export const InvoiceDetail = ({
  invoice,
  isLoading,
  error,
  isUpdating,
  onUpdateStatus,
}: InvoiceDetailProps) => {
  if (isLoading)
    return (
      <Box display="flex" justifyContent="center" py={10}>
        <Spinner size="xl" />
      </Box>
    );
  if (error)
    return (
      <Alert status="error" mt={4}>
        <AlertIcon />
        {error}
      </Alert>
    );
  if (!invoice)
    return (
      <Alert status="warning" mt={4}>
        <AlertIcon />
        No se encontró la factura.
      </Alert>
    );

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Heading size="lg">Detalle de Factura #{invoice.id}</Heading>
        <StatusBadge status={invoice.status} />
      </HStack>
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
        <Card bg="gray.700" color="white">
          <CardHeader>
            <Heading size="md">Información de Facturación</Heading>
          </CardHeader>
          <CardBody as={VStack} spacing={3}>
            <InfoRow
              label="Monto Base"
              value={`$${invoice.base_amount.toFixed(2)}`}
            />
            <InfoRow
              label="Recargo por mora"
              value={`$${invoice.late_fee.toFixed(2)}`}
            />
            <InfoRow
              label="Monto Total"
              value={`$${invoice.total_amount.toFixed(2)}`}
            />
            <InfoRow
              label="Fecha de Emisión"
              value={new Date(invoice.issue_date).toLocaleDateString()}
            />
            <InfoRow
              label="Fecha de Vencimiento"
              value={new Date(invoice.due_date).toLocaleDateString()}
            />
          </CardBody>
        </Card>
        <Card bg="gray.700" color="white">
          <CardHeader>
            <Heading size="md">Información del Cliente</Heading>
          </CardHeader>
          <CardBody as={VStack} spacing={3}>
            <InfoRow
              label="Nombre"
              value={`${invoice.user.firstname} ${invoice.user.lastname}`}
            />
            <InfoRow label="Usuario" value={invoice.user.username} />
          </CardBody>
        </Card>
      </SimpleGrid>

      <Box>
        <Heading size="md" mb={4}>
          Acciones
        </Heading>
        <HStack spacing={4}>
          {invoice.status !== "paid" && (
            <Button
              colorScheme="green"
              onClick={() => onUpdateStatus("paid")}
              isLoading={isUpdating}
            >
              Marcar como Pagada
            </Button>
          )}
          {invoice.receipt_pdf_url && (
            <Button
              colorScheme="blue"
              as="a"
              href={`http://localhost:8000/facturas/${invoice.receipt_pdf_url}`}
              target="_blank"
            >
              Ver Recibo
            </Button>
          )}
        </HStack>
      </Box>
    </VStack>
  );
};
