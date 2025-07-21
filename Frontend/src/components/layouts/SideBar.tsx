import {
  Box,
  Flex,
  Link,
  useColorModeValue,
  Icon,
  useColorMode,
  Button,
} from "@chakra-ui/react";
import { NavLink as RouterLink, useNavigate } from "react-router-dom";
import {
  FiHome,
  FiUser,
  FiBell,
  FiLogOut,
  FiSun,
  FiMoon,
} from "react-icons/fi";

function Sidebar() {
  const navigate = useNavigate();
  const { colorMode, toggleColorMode } = useColorMode();
  const bgColor = useColorModeValue("white", "gray.800");
  const borderColor = useColorModeValue("gray.200", "gray.700");

  const handleLogout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    navigate("/login");
  };

  const NavItem = ({
    icon,
    to,
    children,
  }: {
    icon: any;
    to: string;
    children: React.ReactNode;
  }) => (
    <Link
      as={RouterLink}
      to={to}
      p="3"
      mx="4"
      my="1"
      borderRadius="lg"
      role="group"
      cursor="pointer"
      display="flex"
      alignItems="center"
      _hover={{
        bg: "brand.500",
        color: "white",
      }}
      _activeLink={{
        bg: "brand.500",
        color: "white",
      }}
    >
      {icon && <Icon mr="4" fontSize="16" as={icon} />}
      {children}
    </Link>
  );

  return (
    <Box
      bg={bgColor}
      borderRight="1px"
      borderColor={borderColor}
      w={{ base: "full", md: 60 }}
      pos="fixed"
      h="full"
    >
      <Flex h="20" alignItems="center" mx="8" justifyContent="space-between">
        {/* Aquí puedes poner tu logo */}
      </Flex>
      <NavItem icon={FiHome} to="/dashboard">
        Dashboard
      </NavItem>
      <NavItem icon={FiUser} to="/profile">
        Perfil
      </NavItem>
      <NavItem icon={FiBell} to="/notifications">
        Notificaciones
      </NavItem>
      <Flex
        pos="absolute"
        bottom="10"
        w="full"
        flexDir="column"
        alignItems="center"
      >
        <Button onClick={toggleColorMode} mb="4">
          {colorMode === "light" ? <Icon as={FiMoon} /> : <Icon as={FiSun} />}
        </Button>
        <Button
          leftIcon={<Icon as={FiLogOut} />}
          onClick={handleLogout}
          colorScheme="red"
          variant="ghost"
        >
          Cerrar Sesión
        </Button>
      </Flex>
    </Box>
  );
}

export default Sidebar;
