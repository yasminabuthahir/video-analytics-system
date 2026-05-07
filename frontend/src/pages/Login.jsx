import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Cpu } from "lucide-react";

export default function Login() {
  const [backendUrl, setBackendUrl] = useState(
    localStorage.getItem("backend_url") || "http://localhost:8000"
  );
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      localStorage.setItem("backend_url", backendUrl);
      const form = new FormData();
      form.append("username", username);
      form.append("password", password);
      const res = await axios.post(`${backendUrl}/auth/login`, form);
      localStorage.setItem("token", res.data.access_token);
      localStorage.setItem("role", res.data.role);
      navigate("/");
    } catch {
      setError("Invalid credentials or server unreachable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", background: "#0f1117"
    }}>
      <div className="card" style={{ width: 400 }}>
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <Cpu size={40} color="#3b82f6" />
          <h1 style={{ marginTop: 12, marginBottom: 4 }}>VisionAI</h1>
          <p className="text-muted">Video Analytics System</p>
        </div>

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Backend URL</label>
            <input value={backendUrl} onChange={e => setBackendUrl(e.target.value)}
              placeholder="http://192.168.x.x:8000" />
          </div>
          <div className="form-group">
            <label>Username</label>
            <input value={username} onChange={e => setUsername(e.target.value)}
              placeholder="admin" autoComplete="username" />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••" autoComplete="current-password" />
          </div>
          {error && <p className="text-danger" style={{ marginBottom: "1rem" }}>{error}</p>}
          <button className="btn btn-primary" style={{ width: "100%" }} disabled={loading}>
            {loading ? "Connecting..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}