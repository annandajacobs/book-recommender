import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/recomendacoes", label: "Conversa" },
  { to: "/objetivos", label: "Meus pedidos" },
  { to: "/preferencias", label: "Preferências" },
  { to: "/historico", label: "Histórico" },
];

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
            <span className="wordmark">Book Recommender</span>
            <nav className="nav">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    "nav-link" + (isActive ? " active" : "")
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="nav-user">
            {user && <span className="nav-email">{user.email}</span>}
            <button className="logout-btn" onClick={logout}>
              Sair
            </button>
          </div>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
