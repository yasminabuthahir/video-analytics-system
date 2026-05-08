import { useRef, useState, useEffect } from "react";
import api from "../api";

const COLORS = ["#ef4444", "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"];

export default function ROIDrawer({ cameraId, existingRois = [], onSaved }) {
  const canvasRef = useRef(null);
  const [imgEl, setImgEl] = useState(null);
  const [rois, setRois] = useState(existingRois); // [{points: [[x,y],...], label}]
  const [currentPoints, setCurrentPoints] = useState([]);
  const [drawing, setDrawing] = useState(false);
  const [hoverPos, setHoverPos] = useState(null);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  // Load camera frame as background
  useEffect(() => {
    const backendUrl = localStorage.getItem("backend_url") || "http://localhost:8000";
    const token = localStorage.getItem("token");
    fetch(`${backendUrl}/cameras/${cameraId}/frame`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => {
          setImgEl(img);
          setLoading(false);
        };
        img.src = url;
      })
      .catch(() => setLoading(false));
  }, [cameraId]);

  // Redraw canvas whenever state changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw camera frame background
    if (imgEl) {
      ctx.drawImage(imgEl, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = "#1a1f2e";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#64748b";
      ctx.font = "14px Inter";
      ctx.textAlign = "center";
      ctx.fillText(
        loading ? "Loading camera frame..." : "Could not load frame — drawing on blank canvas",
        canvas.width / 2, canvas.height / 2
      );
    }

    // Draw saved ROIs
    rois.forEach((roi, idx) => {
      if (roi.points.length < 2) return;
      const color = COLORS[idx % COLORS.length];
      ctx.beginPath();
      ctx.moveTo(roi.points[0][0], roi.points[0][1]);
      roi.points.forEach(([x, y]) => ctx.lineTo(x, y));
      ctx.closePath();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.setLineDash([]);
      ctx.stroke();
      ctx.fillStyle = color + "33";
      ctx.fill();
      // Label
      ctx.fillStyle = color;
      ctx.font = "bold 12px Inter";
      ctx.textAlign = "left";
      ctx.fillText(`ROI ${idx + 1}`, roi.points[0][0] + 4, roi.points[0][1] - 6);
      // Draw corner dots
      roi.points.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      });
    });

    // Draw in-progress polygon
    if (currentPoints.length > 0) {
      const color = COLORS[rois.length % COLORS.length];
      ctx.beginPath();
      ctx.moveTo(currentPoints[0][0], currentPoints[0][1]);
      currentPoints.forEach(([x, y]) => ctx.lineTo(x, y));
      if (hoverPos) ctx.lineTo(hoverPos[0], hoverPos[1]);
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
      currentPoints.forEach(([x, y], i) => {
        ctx.beginPath();
        ctx.arc(x, y, i === 0 ? 7 : 5, 0, Math.PI * 2);
        ctx.fillStyle = i === 0 ? "#ffffff" : color;
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    }
  }, [imgEl, rois, currentPoints, hoverPos, loading]);

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    return [
      Math.round((e.clientX - rect.left) * scaleX),
      Math.round((e.clientY - rect.top) * scaleY)
    ];
  };

  const isNearFirst = (pos) => {
    if (currentPoints.length < 3) return false;
    const [fx, fy] = currentPoints[0];
    return Math.abs(pos[0] - fx) < 12 && Math.abs(pos[1] - fy) < 12;
  };

  const handleClick = (e) => {
    const pos = getPos(e);
    if (currentPoints.length > 0 && isNearFirst(pos)) {
      // Close polygon
      finishPolygon();
      return;
    }
    setDrawing(true);
    setCurrentPoints(prev => [...prev, pos]);
  };

  const handleDblClick = () => {
    if (currentPoints.length >= 3) finishPolygon();
  };

  const handleMouseMove = (e) => {
    setHoverPos(getPos(e));
  };

  const finishPolygon = () => {
    if (currentPoints.length < 3) return;
    setRois(prev => [...prev, { points: currentPoints }]);
    setCurrentPoints([]);
    setDrawing(false);
    setHoverPos(null);
  };

  const cancelCurrent = () => {
    setCurrentPoints([]);
    setDrawing(false);
  };

  const deleteRoi = (idx) => {
    setRois(prev => prev.filter((_, i) => i !== idx));
  };

  const saveAllRois = async () => {
    try {
      // Delete all existing first, then re-add
      const existing = existingRois.length;
      for (let i = existing - 1; i >= 0; i--) {
        await api.delete("/config/roi", { data: { camera_id: cameraId, roi_index: i } });
      }
      for (let i = 0; i < rois.length; i++) {
        await api.post("/config/roi", {
          camera_id: cameraId,
          roi_index: i,
          points: rois[i].points
        });
      }
      setMsg(`${rois.length} ROI(s) saved and applied.`);
      setTimeout(() => setMsg(""), 3000);
      if (onSaved) onSaved(rois);
    } catch {
      setMsg("Failed to save ROI.");
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <span className="text-muted" style={{ fontSize: "0.85rem" }}>
          {currentPoints.length === 0
            ? "Click to start drawing a polygon zone"
            : `${currentPoints.length} point(s) — click near first point or double-click to close`}
        </span>
        {drawing && currentPoints.length > 0 && (
          <button className="btn btn-ghost" style={{ padding: "0.2rem 0.6rem", fontSize: "0.8rem" }}
            onClick={cancelCurrent}>Cancel current</button>
        )}
      </div>

      <canvas
        ref={canvasRef}
        width={640} height={360}
        style={{
          borderRadius: 8, cursor: drawing ? "crosshair" : "default",
          display: "block", maxWidth: "100%", border: "1px solid #2d3748"
        }}
        onClick={handleClick}
        onDoubleClick={handleDblClick}
        onMouseMove={handleMouseMove}
      />

      {/* ROI list */}
      {rois.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {rois.map((roi, idx) => (
            <div key={idx} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "0.4rem 0.6rem", background: "#2d3748", borderRadius: 6,
              marginBottom: 6
            }}>
              <span style={{ color: COLORS[idx % COLORS.length], fontWeight: 600, fontSize: "0.85rem" }}>
                ROI {idx + 1} — {roi.points.length} points
              </span>
              <button className="btn btn-danger"
                style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem" }}
                onClick={() => deleteRoi(idx)}>
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center" }}>
        <button className="btn btn-primary" onClick={saveAllRois}
          disabled={rois.length === 0}>
          Save All ROIs
        </button>
        {msg && <span style={{ color: "#10b981", fontSize: "0.85rem" }}>{msg}</span>}
      </div>
    </div>
  );
}