import { useEffect, useState } from "react";
import api from "../api";
import { Users, AlertTriangle, Camera, Activity } from "lucide-react";

function StatCard({ icon, label, value, color }) {
  return (
    <div className="card" style={{ display: "flex", alignItems: "center", gap: 16 }}>
      <div style={{
        background: color + "22", borderRadius: 10, padding: 12, color
      }}>{icon}</div>
      <div>
        <p className="text-muted">{label}</p>
        <p style={{ fontSize: "1.8rem", fontWeight: 700 }}>{value}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [status, setStatus] = useState({ cameras: [] });
  const [alerts, setAlerts] = useState([]);

  const fetchData = async () => {
    try {
      const [s, a] = await Promise.all([
        api.get("/status"),
        api.get("/alerts?limit=5")
      ]);
      setStatus(s.data);
      setAlerts(a.data.alerts);
    } catch {}
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const totalPeople = status.cameras.reduce((sum, cam) => {
    return sum + (cam.latest?.people_counter?.people_count || 0);
  }, 0);

  const totalFaces = status.cameras.reduce((sum, cam) => {
    return sum + (cam.latest?.face_recognizer?.face_count || 0);
  }, 0);

  return (
    <div>
      <h1>Dashboard</h1>

      <div className="grid-3 mb-4">
        <StatCard icon={<Users size={24}/>} label="People Detected" value={totalPeople} color="#3b82f6"/>
        <StatCard icon={<Camera size={24}/>} label="Active Cameras" value={status.cameras.length} color="#10b981"/>
        <StatCard icon={<AlertTriangle size={24}/>} label="Recent Alerts" value={alerts.length} color="#f59e0b"/>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Camera Status</h2>
          {status.cameras.length === 0 && <p className="text-muted">No cameras active</p>}
          {status.cameras.map(cam => (
            <div key={cam.camera_id} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "0.6rem 0", borderBottom: "1px solid #2d3748"
            }}>
              <div>
                <p style={{ fontWeight: 600 }}>{cam.camera_id}</p>
                <p className="text-muted">
                  People: {cam.latest?.people_counter?.people_count ?? 0} |
                  Faces: {cam.latest?.face_recognizer?.face_count ?? 0}
                </p>
              </div>
              <span className="badge badge-green"><Activity size={10}/> Live</span>
            </div>
          ))}
        </div>

        <div className="card">
          <h2>Recent Alerts</h2>
          {alerts.length === 0 && <p className="text-muted">No alerts yet</p>}
          {alerts.map(a => (
            <div key={a.id} style={{
              display: "flex", gap: 12, padding: "0.6rem 0",
              borderBottom: "1px solid #2d3748", alignItems: "flex-start"
            }}>
              {a.snapshot_path && (
                <img
                  src={`${localStorage.getItem("backend_url")}/${a.snapshot_path}`}
                  alt="snapshot"
                  style={{ width: 64, height: 48, objectFit: "cover", borderRadius: 6 }}
                />
              )}
              <div>
                <span className="badge badge-red" style={{ marginBottom: 4 }}>
                  {a.alert_type}
                </span>
                <p style={{ fontSize: "0.85rem" }}>
                  {a.camera_id} · {a.people_count} person(s) · {a.person_label}
                </p>
                <p className="text-muted">{new Date(a.timestamp).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}