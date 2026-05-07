import { useEffect, useState } from "react";
import api from "../api";
import ROIDrawer from "../components/ROIDrawer";
import { Save, ChevronDown, ChevronUp } from "lucide-react";

const MODULE_LABELS = {
  people_counter: "People Counter",
  intrusion_detector: "Intrusion Detector",
  face_recognizer: "Face Recognizer",
  privacy_masker: "Privacy Masker",
};

function Toggle({ checked, onChange }) {
  return (
    <div onClick={onChange} style={{
      width: 44, height: 24, borderRadius: 12,
      background: checked ? "#3b82f6" : "#374151",
      cursor: "pointer", position: "relative", transition: "background 0.2s"
    }}>
      <div style={{
        width: 18, height: 18, borderRadius: "50%", background: "white",
        position: "absolute", top: 3, left: checked ? 23 : 3, transition: "left 0.2s"
      }}/>
    </div>
  );
}

export default function CameraConfig() {
  const [config, setConfig] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [roiExpanded, setRoiExpanded] = useState({});
  const [msg, setMsg] = useState("");
  const role = localStorage.getItem("role");
  const isAdmin = role === "admin";

  useEffect(() => {
    api.get("/config").then(r => setConfig(r.data)).catch(() => {});
  }, []);

  const toggleModule = async (camId, module, current) => {
    if (!isAdmin) return;
    try {
      await api.post("/config/modules", { camera_id: camId, modules: { [module]: !current } });
      const r = await api.get("/config");
      setConfig(r.data);
      setMsg(`${MODULE_LABELS[module]} ${!current ? "enabled" : "disabled"} for ${camId}`);
      setTimeout(() => setMsg(""), 3000);
    } catch {}
  };

  const saveROI = async (camId, roi) => {
    try {
      await api.post("/config/roi", { camera_id: camId, roi });
      setMsg(`ROI saved for ${camId}. Restart backend to apply.`);
      setTimeout(() => setMsg(""), 4000);
    } catch {}
  };

  if (!config) return <p className="text-muted">Loading config...</p>;

  return (
    <div>
      <h1>Camera Configuration</h1>
      {msg && (
        <div className="card" style={{ background: "#14532d", borderColor: "#16a34a", marginBottom: "1rem" }}>
          {msg}
        </div>
      )}
      {!isAdmin && (
        <div className="card" style={{ background: "#1e3a5f22", borderColor: "#3b82f6", marginBottom: "1rem" }}>
          <p className="text-muted">You have viewer access — changes are disabled.</p>
        </div>
      )}

      {config.cameras.map(cam => (
        <div className="card" key={cam.camera_id}>
          <div className="flex justify-between items-center"
            style={{ cursor: "pointer" }}
            onClick={() => setExpanded(e => ({ ...e, [cam.camera_id]: !e[cam.camera_id] }))}>
            <div>
              <h2 style={{ marginBottom: 2 }}>{cam.name || cam.camera_id}</h2>
              <p className="text-muted">Source: {cam.source}</p>
            </div>
            {expanded[cam.camera_id] ? <ChevronUp size={20}/> : <ChevronDown size={20}/>}
          </div>

          {expanded[cam.camera_id] && (
            <div style={{ marginTop: "1rem" }}>
              <h2>Modules</h2>
              {Object.entries(MODULE_LABELS).map(([key, label]) => (
                <div key={key} className="flex justify-between items-center"
                  style={{ padding: "0.6rem 0", borderBottom: "1px solid #2d3748" }}>
                  <span>{label}</span>
                  <Toggle
                    checked={!!cam.modules[key]}
                    onChange={() => toggleModule(cam.camera_id, key, cam.modules[key])}
                  />
                </div>
              ))}

              {isAdmin && (
                <div style={{ marginTop: "1.5rem" }}>
                  <div className="flex justify-between items-center" style={{ marginBottom: 12 }}>
                    <h2 style={{ marginBottom: 0 }}>Intrusion ROI</h2>
                    <button className="btn btn-ghost"
                      onClick={() => setRoiExpanded(r => ({ ...r, [cam.camera_id]: !r[cam.camera_id] }))}>
                      {roiExpanded[cam.camera_id] ? "Hide" : "Draw ROI"}
                    </button>
                  </div>
                  <p className="text-muted" style={{ marginBottom: 8 }}>
                    Current: [{cam.intrusion_roi?.join(", ") || "not set"}]
                  </p>
                  {roiExpanded[cam.camera_id] && (
                    <ROIDrawer cameraId={cam.camera_id} onSave={(roi) => saveROI(cam.camera_id, roi)} />
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}