import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

// Define la estructura de la respuesta del backend
type LoginProcessResponse = {
  success: boolean;
  access_token?: string;
  token_type?: string;
  message?: string;
};

function Login() {
  // URL del endpoint de login en tu backend
  const LOGIN_URL = "http://localhost:8000/api/users/login";

  // Referencias para los inputs del formulario
  const userInputRef = useRef<HTMLInputElement>(null);
  const passInputRef = useRef<HTMLInputElement>(null);

  // Estado para manejar los mensajes al usuario
  const [message, setMessage] = useState<string | null>(null);

  // Hook para navegar a otras rutas
  const navigate = useNavigate();

  // Procesa la respuesta del backend
  function loginProcess(dataObject: LoginProcessResponse) {
    if (dataObject.success && dataObject.access_token) {
      localStorage.setItem("token", dataObject.access_token);
      // Podrías guardar también datos del usuario si el backend los devolviera
      setMessage("Iniciando sesión...");
      navigate("/dashboard"); // Redirige al dashboard
    } else {
      setMessage(dataObject.message ?? "Error desconocido");
    }
  }

  // Maneja el envío del formulario
  function handleLogin(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); // Evita que la página se recargue

    const username = userInputRef.current?.value ?? "";
    const password = passInputRef.current?.value ?? "";

    const requestOptions = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    };

    fetch(LOGIN_URL, requestOptions)
      .then((response) => response.json())
      .then((data: LoginProcessResponse) => loginProcess(data))
      .catch((error) => {
        console.error("Error en el fetch:", error);
        setMessage("No se pudo conectar con el servidor.");
      });
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        className="card p-4 shadow-lg"
        style={{ maxWidth: "400px", width: "100%" }}
      >
        <h1 className="text-center mb-3">Login</h1>
        <form onSubmit={handleLogin}>
          <div className="mb-3">
            <label htmlFor="inputUser" className="form-label">
              Usuario
            </label>
            <input
              type="text"
              className="form-control"
              id="inputUser"
              ref={userInputRef}
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="inputPassword">Contraseña</label>
            <input
              type="password"
              className="form-control"
              id="inputPassword"
              ref={passInputRef}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary w-100">
            Ingresar
          </button>
          {message && <div className="mt-3 text-center">{message}</div>}
        </form>
      </div>
    </div>
  );
}

export default Login;
