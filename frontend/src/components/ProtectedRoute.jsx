import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Loader from "./Loader";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return <Loader label="Carregando sua conta…" />;
  if (!user) return <Navigate to="/entrar" replace />;

  return children;
}
