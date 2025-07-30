// src/context/AuthContext.tsx
import {
  createContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from "react";
import { jwtDecode, JwtPayload } from "jwt-decode"; // Usamos jwt-decode para verificar la expiración

// 1. Definimos la nueva estructura del objeto User
export interface User {
  first_name: string;
  role: "administrador" | "cliente"; // Roles simplificados
  username: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

// Creamos el contexto con valores por defecto
export const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  loading: true,
  login: () => {},
  logout: () => {},
});

// 2. Simplificamos el AuthProvider
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("token")
  );
  const [loading, setLoading] = useState(true);

  // La función de logout es más explícita
  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }, []);

  // 3. El useEffect ahora es más robusto
  useEffect(() => {
    if (token) {
      try {
        const decodedToken = jwtDecode<JwtPayload>(token);
        // Verificamos si el token ha expirado
        if (decodedToken.exp! * 1000 < Date.now()) {
          logout();
        } else {
          // Si el token es válido, recuperamos los datos del usuario
          const storedUser = localStorage.getItem("user");
          if (storedUser) {
            setUser(JSON.parse(storedUser));
          } else {
            // Si no hay datos de usuario, es un estado inconsistente, así que cerramos sesión
            logout();
          }
        }
      } catch (error) {
        console.error("Token inválido:", error);
        logout();
      }
    }
    setLoading(false);
  }, [token, logout]);

  // 4. Creamos una función de login para ser llamada desde el componente Login
  const login = (newToken: string, newUser: User) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
