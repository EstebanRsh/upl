// src/components/payments/InvoiceFilter.tsx
import { HStack, Select, Button } from "@chakra-ui/react";
import { useState } from "react";

interface InvoiceFilterProps {
  onFilterChange: (month: string, year: string) => void;
}

export const InvoiceFilter = ({ onFilterChange }: InvoiceFilterProps) => {
  const [month, setMonth] = useState("");
  const [year, setYear] = useState("");

  const handleFilter = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange(month, year);
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);
  const months = [
    { v: "1", l: "Enero" },
    { v: "2", l: "Febrero" },
    { v: "3", l: "Marzo" },
    { v: "4", l: "Abril" },
    { v: "5", l: "Mayo" },
    { v: "6", l: "Junio" },
    { v: "7", l: "Julio" },
    { v: "8", l: "Agosto" },
    { v: "9", l: "Septiembre" },
    { v: "10", l: "Octubre" },
    { v: "11", l: "Noviembre" },
    { v: "12", l: "Diciembre" },
  ];

  // Estilo para las opciones del menú desplegable
  const optionStyle = { backgroundColor: "#2D3748" };

  return (
    <HStack
      as="form"
      onSubmit={handleFilter}
      spacing={3}
      w={{ base: "100%", md: "auto" }}
    >
      {/* --- INICIO DE LA CORRECCIÓN CLAVE --- */}
      <Select
        value={month}
        onChange={(e) => setMonth(e.target.value)}
        bg="gray.700"
        // Cambiamos el color del texto del placeholder para que coincida
        color={month ? "white" : "gray.400"}
      >
        <option value="" style={optionStyle}>
          Filtrar por mes
        </option>
        {months.map((m) => (
          <option key={m.v} value={m.v} style={optionStyle}>
            {m.l}
          </option>
        ))}
      </Select>
      <Select
        value={year}
        onChange={(e) => setYear(e.target.value)}
        bg="gray.700"
        color={year ? "white" : "gray.400"}
      >
        <option value="" style={optionStyle}>
          Filtrar por año
        </option>
        {years.map((y) => (
          <option key={y} value={y} style={optionStyle}>
            {y}
          </option>
        ))}
      </Select>
      {/* --- FIN DE LA CORRECCIÓN CLAVE --- */}
      <Button type="submit" colorScheme="teal">
        Buscar
      </Button>
    </HStack>
  );
};
