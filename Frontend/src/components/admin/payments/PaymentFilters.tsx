// src/components/admin/payments/PaymentFilters.tsx
import { useState, useEffect } from "react";
import {
  HStack,
  Input,
  Select,
  Button,
  SimpleGrid,
  FormControl,
  FormLabel,
  Box, // <-- Importamos Box para el formulario
} from "@chakra-ui/react";
import { Filters } from "../../../views/admin/PaymentManagement";

interface PaymentFiltersProps {
  onFilterChange: (filters: Partial<Filters>) => void;
  onResetFilters: () => void;
  initialFilters: Filters;
}

export const PaymentFilters = ({
  onFilterChange,
  onResetFilters,
  initialFilters,
}: PaymentFiltersProps) => {
  const [filters, setFilters] = useState(initialFilters);

  useEffect(() => {
    setFilters(initialFilters);
  }, [initialFilters]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange(filters);
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 6 }, (_, i) => currentYear - i);
  const months = [
    { value: "1", label: "Enero" },
    { value: "2", label: "Febrero" },
    { value: "3", label: "Marzo" },
    { value: "4", label: "Abril" },
    { value: "5", label: "Mayo" },
    { value: "6", label: "Junio" },
    { value: "7", label: "Julio" },
    { value: "8", label: "Agosto" },
    { value: "9", label: "Septiembre" },
    { value: "10", label: "Octubre" },
    { value: "11", label: "Noviembre" },
    { value: "12", label: "Diciembre" },
  ];

  return (
    <Box as="form" onSubmit={handleApplyFilters} w="100%">
      {/* --- CORRECCIÓN AQUÍ --- */}
      <SimpleGrid
        columns={{ base: 1, md: 2, lg: 5 }}
        spacing={4}
        alignItems="end"
      >
        <FormControl>
          <FormLabel>Buscar Cliente</FormLabel>
          <Input
            name="search"
            placeholder="Nombre, Apellido o DNI..."
            value={filters.search}
            onChange={handleInputChange}
            bg="gray.700"
          />
        </FormControl>

        <FormControl>
          <FormLabel>Mes</FormLabel>
          <Select
            name="month"
            placeholder="Todos"
            value={filters.month}
            onChange={handleInputChange}
            bg="gray.700"
          >
            {months.map((m) => (
              <option
                key={m.value}
                value={m.value}
                style={{ backgroundColor: "#2D3748" }}
              >
                {m.label}
              </option>
            ))}
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel>Año</FormLabel>
          <Select
            name="year"
            placeholder="Todos"
            value={filters.year}
            onChange={handleInputChange}
            bg="gray.700"
          >
            {years.map((y) => (
              <option key={y} value={y} style={{ backgroundColor: "#2D3748" }}>
                {y}
              </option>
            ))}
          </Select>
        </FormControl>

        <FormControl>
          <FormLabel>Método de Pago</FormLabel>
          <Select
            name="payment_method"
            placeholder="Todos"
            value={filters.payment_method}
            onChange={handleInputChange}
            bg="gray.700"
          >
            <option value="Efectivo" style={{ backgroundColor: "#2D3748" }}>
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

        <HStack>
          <Button type="submit" colorScheme="blue" flex={1}>
            Filtrar
          </Button>
          <Button onClick={onResetFilters} flex={1}>
            Limpiar
          </Button>
        </HStack>
      </SimpleGrid>
    </Box>
  );
};
