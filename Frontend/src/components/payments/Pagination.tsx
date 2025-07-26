// src/components/payments/Pagination.tsx
import { HStack, Button, Icon, Text } from "@chakra-ui/react";
import { FaChevronLeft, FaChevronRight } from "react-icons/fa";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading: boolean;
}

export const Pagination = ({
  currentPage,
  totalPages,
  onPageChange,
  isLoading,
}: PaginationProps) => {
  if (totalPages <= 1) {
    return null; // No muestra nada si solo hay una página
  }

  return (
    <HStack justify="center" mt={4}>
      <Button
        onClick={() => onPageChange(currentPage - 1)}
        isDisabled={isLoading || currentPage === 1}
        leftIcon={<Icon as={FaChevronLeft} />}
        size="sm"
      >
        Anterior
      </Button>
      <Text>
        Página {currentPage} de {totalPages}
      </Text>
      <Button
        onClick={() => onPageChange(currentPage + 1)}
        isDisabled={isLoading || currentPage === totalPages}
        rightIcon={<Icon as={FaChevronRight} />}
        size="sm"
      >
        Siguiente
      </Button>
    </HStack>
  );
};
