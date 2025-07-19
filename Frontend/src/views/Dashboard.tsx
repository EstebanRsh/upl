import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    // Podrías también borrar otros datos del usuario si los guardaste
    navigate("/login");
  };

  // Aquí podrías obtener el nombre del usuario desde el token o localStorage
  const userName = "Estudiante";

  return (
    <div>
      <h2>Dashboard</h2>
      <p>¡Bienvenido, {userName}!</p>
      <button onClick={handleLogout} className="btn btn-danger">
        Cerrar sesión
      </button>
    </div>
  );
}

export default Dashboard;
