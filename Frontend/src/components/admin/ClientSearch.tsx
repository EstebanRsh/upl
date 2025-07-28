// src/components/admin/ClientSearch.tsx
import { HStack, Input, Button } from "@chakra-ui/react";
import { useState } from "react";

interface ClientSearchProps {
  onSearch: (searchTerm: string) => void;
}

export const ClientSearch = ({ onSearch }: ClientSearchProps) => {
  const [term, setTerm] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(term);
  };

  return (
    <HStack as="form" onSubmit={handleSearch} w={{ base: "100%", md: "auto" }}>
      <Input
        placeholder="Buscar por nombre de usuario..."
        bg="gray.700"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
      />
      <Button type="submit" colorScheme="teal">
        Buscar
      </Button>
    </HStack>
  );
};
