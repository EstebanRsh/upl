// src/context/AuthContext.tsx
import { createContext, useState, useEffect, ReactNode } from "react";
import { jwtDecode } from "jwt-decode";

interface User {
  first_name: string;
  role: string;
  user_id: number;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  logout: () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const decodedToken: any = jwtDecode(token);

        // --- INICIO DE LA CORRECCIÓN CLAVE ---
        // Validamos que el token contenga la información mínima necesaria
        if (decodedToken && decodedToken.role && decodedToken.user_id) {
          const userData: User = {
            first_name: decodedToken.first_name || "Usuario", // Valor por defecto por si acaso
            role: decodedToken.role,
            user_id: decodedToken.user_id,
          };
          setUser(userData);
          localStorage.setItem("user", JSON.stringify(userData));
        } else {
          // Si el token no tiene la forma esperada, lo consideramos inválido
          throw new Error("Token con formato inválido.");
        }
        // --- FIN DE LA CORRECCIÓN CLAVE ---
      } catch (error) {
        console.error("Error al procesar el token:", error);
        setUser(null);
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      }
    }
    setLoading(false);
  }, []);

  const logout = () => {
    setUser(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
