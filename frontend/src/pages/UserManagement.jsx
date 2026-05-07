import { useEffect, useState } from "react";
import api from "../api";
import { Trash2 } from "lucide-react";

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ username: "", password: "", role: "viewer" });
  const [msg, setMsg] = useState("");

  const fetchUsers = () => api.get("/users").then(r => setUsers(r.data.users)).catch(() => {});

  useEffect(() => { fetchUsers(); }, []);

  const addUser = async () => {
    try {
      await api.post("/users", form);
      setMsg("User created successfully");
      setForm({ username: "", password: "", role: "viewer" });
      fetchUsers();
    } catch (e) {
      setMsg(e.response?.data?.detail || "Error creating user");
    }
  };

  const deleteUser = async (username) => {
    if (!confirm(`Delete user "${username}"?`)) return;
    await api.delete(`/users/${username}`);
    fetchUsers();
  };

  return (
    <div>
      <h1>User Management</h1>
      <div className="grid-2">
        <div className="card">
          <h2>Add User</h2>
          <div className="form-group">
            <label>Username</label>
            <input value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
          </div>
          <div className="form-group">
            <label>Role</label>
            <select value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {msg && <p style={{ marginBottom: "1rem", color: msg.includes("success") ? "#10b981" : "#f87171" }}>{msg}</p>}
          <button className="btn btn-primary" onClick={addUser}>Create User</button>
        </div>

        <div className="card">
          <h2>Existing Users</h2>
          <table>
            <thead><tr><th>Username</th><th>Role</th><th></th></tr></thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td><span className={`badge ${u.role === "admin" ? "badge-blue" : "badge-gray"}`}>{u.role}</span></td>
                  <td>
                    {u.username !== "admin" && (
                      <button className="btn btn-danger" style={{ padding: "0.3rem 0.6rem" }}
                        onClick={() => deleteUser(u.username)}>
                        <Trash2 size={14} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}