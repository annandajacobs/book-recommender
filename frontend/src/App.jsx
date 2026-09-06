import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import GoalsPage from "./pages/GoalsPage";
import PreferencesPage from "./pages/PreferencesPage";
import RecommendationsPage from "./pages/RecommendationsPage";
import HistoryPage from "./pages/HistoryPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/entrar" element={<LoginPage />} />
          <Route path="/registrar" element={<RegisterPage />} />

          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/recomendacoes" element={<RecommendationsPage />} />
            <Route path="/objetivos" element={<GoalsPage />} />
            <Route path="/preferencias" element={<PreferencesPage />} />
            <Route path="/historico" element={<HistoryPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/recomendacoes" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
