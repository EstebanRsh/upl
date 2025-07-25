// src/components/layouts/MainLayout.tsx
import { Outlet } from "react-router-dom";
import { Box } from "@chakra-ui/react";
import Navbar from "./Navbar";

export default function MainLayout() {
  return (
    <Box>
      <Navbar />
      <main>
        {/* Outlet es el componente de react-router que renderiza la ruta hija */}
        <Outlet />
      </main>
    </Box>
  );
}
