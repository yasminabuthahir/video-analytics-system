import { useEffect, useState } from "react";
import api from "../api";

export default function AlertHistory() {
  const [alerts, setAlerts] = useState([]);
  const [limit, setLimit] = useState(50);
  const backendUrl = localStorage.getItem("backend_url");

  useEffect(() => {
    api.get(`/alerts?limit=${limit}`).then(r => setAlerts(r.data.alerts)).catch(() => {});
  }, [limit]);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1>Alert History</h1>
        <select value={limit} onChange={e => setLimit(e.target.value)}
          style={{ width: 120 }}>
          <option value={25}>Last 25</option>
          <option value={50}>Last 50</option>
          <option value={100}>Last 100</option>
        </select>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table>
          <thead>
            <tr>
              <th>Snapshot</th>
              <th>ID</th>
              <th>Camera</th>
              <th>Type</th>
              <th>People</th>
              <th>Label</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map(a => (
              <tr key={a.id}>
                <td>
                  {a.snapshot_path ? (
                    <img
                      src={`${backendUrl}/${a.snapshot_path}`}
                      alt="snap"
                      style={{ width: 80, height: 50, objectFit: "cover", borderRadius: 4 }}
                    />
                  ) : <span className="text-muted">—</span>}
                </td>
                <td>{a.id}</td>
                <td>{a.camera_id}</td>
                <td><span className="badge badge-red">{a.alert_type}</span></td>
                <td>{a.people_count}</td>
                <td>{a.person_label}</td>
                <td>{new Date(a.timestamp).toLocaleString()}</td>
              </tr>
            ))}
            {alerts.length === 0 && (
              <tr><td colSpan={7} style={{ textAlign: "center", padding: "2rem" }}>
                No alerts found
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}