import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  colors: {
    brand: {
      50: '#e6f7ff',
      100: '#b3e0ff',
      200: '#80c9ff',
      300: '#4daeff',
      400: '#1a93ff',
      500: '#007bff', // Color principal del logo "Up"
      600: '#0062cc',
      700: '#004c99',
      800: '#003566',
      900: '#001f33',
    },
  },
  fonts: {
    heading: `'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', sans-serif`, // Tipografía profesional
    body: `'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', sans-serif`,
  },
});

export default theme;