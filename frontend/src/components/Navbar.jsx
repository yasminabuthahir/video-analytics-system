import { NavLink, useNavigate } from "react-router-dom";
import { LayoutDashboard, Camera, Bell, Users, LogOut, Cpu } from "lucide-react";

export default function Navbar() {
  const navigate = useNavigate();
  const role = localStorage.getItem("role");

  const logout = () => {
    localStorage.clear();
    navigate("/login");
  };

  const links = [
    { to: "/", icon: <LayoutDashboard size={18} />, label: "Dashboard" },
    { to: "/config", icon: <Camera size={18} />, label: "Cameras" },
    { to: "/alerts", icon: <Bell size={18} />, label: "Alerts" },
    ...(role === "admin" ? [{ to: "/users", icon: <Users size={18} />, label: "Users" }] : []),
  ];

  return (
    <nav style={{
      width: 220, background: "#111827", borderRight: "1px solid #1f2937",
      display: "flex", flexDirection: "column", padding: "1.5rem 1rem"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: "2rem" }}>
        <Cpu size={24} color="#3b82f6" />
        <span style={{ fontWeight: 700, fontSize: "1rem", color: "#f1f5f9" }}>VisionAI</span>
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
        {links.map(l => (
          <NavLink key={l.to} to={l.to} end={l.to === "/"} style={({ isActive }) => ({
            display: "flex", alignItems: "center", gap: 10,
            padding: "0.6rem 0.8rem", borderRadius: 8,
            color: isActive ? "#3b82f6" : "#94a3b8",
            background: isActive ? "#1e3a5f22" : "transparent",
            textDecoration: "none", fontSize: "0.9rem", fontWeight: 500,
            transition: "all 0.15s"
          })}>
            {l.icon} {l.label}
          </NavLink>
        ))}
      </div>

      <button onClick={logout} className="btn btn-ghost"
        style={{ display: "flex", alignItems: "center", gap: 8, marginTop: "auto" }}>
        <LogOut size={16} /> Logout
      </button>
    </nav>
  );
}