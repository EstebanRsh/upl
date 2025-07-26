// src/components/payments/InvoiceList.tsx
import {
  Box,
  Text,
  VStack,
  Badge,
  Button,
  Icon,
  HStack,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  useBreakpointValue,
  Card,
  CardBody,
  Heading,
  Link as ChakraLink,
} from "@chakra-ui/react";
import { FaFilePdf, FaUpload, FaEye } from "react-icons/fa";
import { Invoice } from "../../views/PaymentHistory";

// --- Sub-componentes visuales ---
const StatusBadge = ({ status }: { status: Invoice["status"] }) => {
  const statusConfig = {
    paid: { s: "green", t: "Pagada" },
    overdue: { s: "red", t: "Vencida" },
    in_review: { s: "cyan", t: "En Verificación" },
    pending: { s: "yellow", t: "Pendiente" },
  };
  const config = statusConfig[status] || statusConfig.pending;
  return <Badge colorScheme={config.s}>{config.t}</Badge>;
};

const ActionButtons = ({
  invoice,
  onUploadClick,
  onDownloadClick,
  isMobile,
}: {
  invoice: Invoice;
  onUploadClick: (id: number) => void;
  onDownloadClick: (id: number) => void;
  isMobile?: boolean;
}) => (
  <Box
    minHeight={{ base: "auto", md: "32px" }}
    display="flex"
    alignItems="center"
  >
    <HStack spacing={2} w={isMobile ? "100%" : "auto"}>
      {invoice.status === "paid" && invoice.receipt_pdf_url && (
        <Button
          onClick={() => onDownloadClick(invoice.id)}
          size="sm"
          colorScheme="blue"
          leftIcon={<Icon as={FaFilePdf} />}
          flexGrow={isMobile ? 1 : 0}
        >
          Recibo
        </Button>
      )}
      {invoice.user_receipt_url && (
        <Button
          as={ChakraLink}
          href={`http://localhost:8000/${invoice.user_receipt_url}`}
          isExternal
          size="sm"
          variant="outline"
          leftIcon={<Icon as={FaEye} />}
          flexGrow={isMobile ? 1 : 0}
        >
          Comprobante
        </Button>
      )}
      {(invoice.status === "pending" || invoice.status === "overdue") && (
        <Button
          size="sm"
          colorScheme="orange"
          leftIcon={<Icon as={FaUpload} />}
          onClick={() => onUploadClick(invoice.id)}
          flexGrow={isMobile ? 1 : 0}
        >
          Subir
        </Button>
      )}
    </HStack>
  </Box>
);

const InvoiceTableRow = ({
  invoice,
  onUploadClick,
  onDownloadClick,
}: {
  invoice: Invoice;
  onUploadClick: (id: number) => void;
  onDownloadClick: (id: number) => void;
}) => (
  <Tr>
    <Td fontWeight="medium">#{invoice.id}</Td>
    <Td>{new Date(invoice.issue_date).toLocaleDateString()}</Td>
    <Td>{new Date(invoice.due_date).toLocaleDateString()}</Td>
    <Td isNumeric>${invoice.total_amount.toFixed(2)}</Td>
    <Td>
      <StatusBadge status={invoice.status} />
    </Td>
    <Td>
      <ActionButtons
        invoice={invoice}
        onUploadClick={onUploadClick}
        onDownloadClick={onDownloadClick}
      />
    </Td>
  </Tr>
);

const InvoiceCard = ({
  invoice,
  onUploadClick,
  onDownloadClick,
}: {
  invoice: Invoice;
  onUploadClick: (id: number) => void;
  onDownloadClick: (id: number) => void;
}) => (
  <Card bg="gray.700" w="100%">
    <CardBody>
      <HStack justify="space-between" mb={4}>
        <Heading size="sm" color="whiteAlpha.900">
          Factura #{invoice.id}
        </Heading>
        <StatusBadge status={invoice.status} />
      </HStack>
      <VStack align="stretch" spacing={2} mb={5}>
        <HStack justify="space-between">
          <Text color="gray.400">Monto:</Text>
          <Text fontWeight="bold" fontSize="lg" color="whiteAlpha.900">
            ${invoice.total_amount.toFixed(2)}
          </Text>
        </HStack>
        <HStack justify="space-between">
          <Text color="gray.400">Vencimiento:</Text>
          <Text color="whiteAlpha.900">
            {new Date(invoice.due_date).toLocaleDateString()}
          </Text>
        </HStack>
      </VStack>
      <ActionButtons
        invoice={invoice}
        onUploadClick={onUploadClick}
        onDownloadClick={onDownloadClick}
        isMobile
      />
    </CardBody>
  </Card>
);

interface InvoiceListProps {
  invoices: Invoice[];
  onUploadClick: (id: number) => void;
  onDownloadClick: (id: number) => void;
  isLoading: boolean;
}

export const InvoiceList = ({
  invoices,
  onUploadClick,
  onDownloadClick,
  isLoading,
}: InvoiceListProps) => {
  const isMobile = useBreakpointValue({ base: true, md: false });

  const listStyles = {
    opacity: isLoading ? 0.5 : 1,
    transition: "opacity 0.3s ease-in-out",
    pointerEvents: isLoading ? "none" : "auto",
    minHeight: "420px",
  };

  if (invoices.length === 0) {
    return (
      <Box
        sx={listStyles}
        display="flex"
        alignItems="center"
        justifyContent="center"
        bg="gray.700"
        borderRadius="md"
      >
        <Text color="gray.400" p={4}>
          No se encontraron facturas con los filtros seleccionados.
        </Text>
      </Box>
    );
  }

  return isMobile ? (
    <VStack spacing={4} sx={listStyles}>
      {invoices.map((invoice) => (
        <InvoiceCard
          key={invoice.id}
          invoice={invoice}
          onUploadClick={onUploadClick}
          onDownloadClick={onDownloadClick}
        />
      ))}
    </VStack>
  ) : (
    <TableContainer bg="gray.700" borderRadius="md" sx={listStyles}>
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th color="white">N°</Th>
            <Th color="white">Emisión</Th>
            <Th color="white">Vencimiento</Th>
            <Th isNumeric color="white">
              Monto
            </Th>
            <Th color="white">Estado</Th>
            <Th color="white">Acciones</Th>
          </Tr>
        </Thead>
        <Tbody>
          {invoices.map((invoice) => (
            <InvoiceTableRow
              key={invoice.id}
              invoice={invoice}
              onUploadClick={onUploadClick}
              onDownloadClick={onDownloadClick}
            />
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  );
};
