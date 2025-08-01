// src/components/admin/payments/PaymentList.tsx
import {
  Box,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  IconButton,
} from "@chakra-ui/react";
import { DownloadIcon } from "@chakra-ui/icons";
import { Payment } from "../../../views/admin/PaymentManagement"; // Importamos el tipo desde la vista principal

interface PaymentListProps {
  payments: Payment[];
}

export const PaymentList = ({ payments }: PaymentListProps) => {
  if (payments.length === 0) {
    return (
      <Box bg="gray.700" p={6} borderRadius="md" textAlign="center">
        <Text color="gray.400">
          No se encontraron pagos con los filtros seleccionados.
        </Text>
      </Box>
    );
  }

  const getMethodColorScheme = (method: string) => {
    if (method?.toLowerCase().includes("efectivo")) return "green";
    if (method?.toLowerCase().includes("transferencia")) return "blue";
    return "gray";
  };

  return (
    <TableContainer bg="gray.700" borderRadius="md">
      <Table variant="simple" color="white">
        <Thead>
          <Tr>
            <Th color="gray.400">Cliente</Th>
            <Th color="gray.400">Fecha de Pago</Th>
            <Th color="gray.400" isNumeric>
              Monto
            </Th>
            <Th color="gray.400">Método</Th>
            <Th color="gray.400">Factura ID</Th>
            <Th color="gray.400">Acciones</Th>
          </Tr>
        </Thead>
        <Tbody>
          {payments.map((payment) => (
            <Tr key={payment.id}>
              <Td>
                {payment.user.firstname} {payment.user.lastname}
              </Td>
              <Td>{new Date(payment.payment_date).toLocaleDateString()}</Td>
              <Td isNumeric>${payment.amount.toFixed(2)}</Td>
              <Td>
                <Badge
                  colorScheme={getMethodColorScheme(payment.payment_method)}
                >
                  {payment.payment_method || "N/A"}
                </Badge>
              </Td>
              <Td>#{payment.invoice_id}</Td>
              <Td>
                <IconButton
                  aria-label="Descargar Recibo"
                  icon={<DownloadIcon />}
                  size="sm"
                  variant="ghost"
                  // onClick={() => onDownload(payment.id)} // Funcionalidad futura
                />
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );
};
