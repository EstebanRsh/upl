import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// 1. Importa las herramientas de Chakra UI
import { ChakraProvider, extendTheme } from "@chakra-ui/react";

// 2. Crea un tema básico (puedes personalizarlo después)
const theme = extendTheme({
  colors: {
    brand: {
      500: "#007bff", // Tu color principal
    },
  },
});

// 3. Renderiza tu aplicación
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    {/* 4. Envuelve tu App con ChakraProvider y pásale el tema */}
    <ChakraProvider theme={theme}>
      <App />
    </ChakraProvider>
  </React.StrictMode>
);
