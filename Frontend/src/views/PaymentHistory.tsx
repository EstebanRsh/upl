import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Spinner,
  Text,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";

// Definimos la estructura de un objeto de pago, basándonos en tu backend
interface Payment {
  id_pago: number;
  monto: number;
  "afecha de pago": string; // Mantenemos el nombre del campo como en tu backend
  mes_pagado: string;
}

function PaymentHistory() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPayments = async () => {
      //const token = localStorage.getItem('token');
      // Cuando tu backend esté listo, reemplazarás esto con el fetch real
      // const PAYMENTS_URL = "http://localhost:8000/payment/user";

      try {
        // --- INICIO: DATOS DE EJEMPLO (reemplazar con fetch) ---
        await new Promise((resolve) => setTimeout(resolve, 1000)); // Simula retraso de red
        const mockData: Payment[] = [
          {
            id_pago: 1,
            monto: 3500.5,
            "afecha de pago": "2025-07-10T14:30:00Z",
            mes_pagado: "2025-07-01",
          },
          {
            id_pago: 2,
            monto: 3500.5,
            "afecha de pago": "2025-06-09T11:00:00Z",
            mes_pagado: "2025-06-01",
          },
          {
            id_pago: 3,
            monto: 3400.0,
            "afecha de pago": "2025-05-11T10:15:00Z",
            mes_pagado: "2025-05-01",
          },
        ];
        setPayments(mockData);
        // --- FIN: DATOS DE EJEMPLO ---

        /* --- CÓDIGO FETCH REAL (para cuando lo conectes) ---
        if (!token) {
          throw new Error("No se pudo verificar la sesión.");
        }
        const response = await fetch(PAYMENTS_URL, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'No se pudieron cargar los pagos.');
        }
        const data = await response.json();
        setPayments(data);
        */
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPayments();
  }, []);

  // Funciones para formatear los datos y que se vean mejor
  const formatCurrency = (amount: number) => {
    return amount.toLocaleString("es-AR", {
      style: "currency",
      currency: "ARS",
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-AR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatMonth = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("es-AR", {
      year: "numeric",
      month: "long",
      timeZone: "UTC", // Importante para evitar corrimientos de día
    });
  };

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="60vh"
      >
        <Spinner size="xl" />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={8}>
        <Alert status="error">
          <AlertIcon />
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={8}>
      <Heading as="h1" size="xl" mb={6}>
        Historial de Pagos
      </Heading>
      <TableContainer bg="gray.700" color="white" borderRadius="md">
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th color="white">Mes Correspondiente</Th>
              <Th color="white">Fecha de Pago</Th>
              <Th isNumeric color="white">
                Monto
              </Th>
            </Tr>
          </Thead>
          <Tbody>
            {payments.length > 0 ? (
              payments.map((pay) => (
                <Tr key={pay.id_pago}>
                  <Td>{formatMonth(pay.mes_pagado)}</Td>
                  <Td>{formatDate(pay["afecha de pago"])}</Td>
                  <Td isNumeric fontWeight="bold">
                    {formatCurrency(pay.monto)}
                  </Td>
                </Tr>
              ))
            ) : (
              <Tr>
                <Td colSpan={3} textAlign="center">
                  <Text p={4}>No tienes pagos registrados.</Text>
                </Td>
              </Tr>
            )}
          </Tbody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default PaymentHistory;
