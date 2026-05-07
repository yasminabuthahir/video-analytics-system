import { useRef, useState, useEffect } from "react";

export default function ROIDrawer({ cameraId, onSave }) {
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [start, setStart] = useState(null);
  const [roi, setRoi] = useState(null);

  // Draw a placeholder background
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#1a1f2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#4a5568";
    ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);
    ctx.fillStyle = "#64748b";
    ctx.font = "14px Inter";
    ctx.textAlign = "center";
    ctx.fillText("Click and drag to draw ROI zone", canvas.width / 2, canvas.height / 2);
  }, []);

  const getPos = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    return [Math.round(e.clientX - rect.left), Math.round(e.clientY - rect.top)];
  };

  const redraw = (x1, y1, x2, y2) => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#1a1f2e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#4a5568";
    ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);
    // Draw ROI
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 3]);
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.fillStyle = "#ef444422";
    ctx.fillRect(x1, y1, x2 - x1, y2 - y1);
    ctx.setLineDash([]);
    ctx.fillStyle = "#ef4444";
    ctx.font = "12px Inter";
    ctx.fillText("Restricted Zone", x1 + 6, y1 + 16);
  };

  const onMouseDown = (e) => {
    setDrawing(true);
    setStart(getPos(e));
  };

  const onMouseMove = (e) => {
    if (!drawing || !start) return;
    const [cx, cy] = getPos(e);
    redraw(start[0], start[1], cx, cy);
  };

  const onMouseUp = (e) => {
    if (!drawing || !start) return;
    const [cx, cy] = getPos(e);
    const newRoi = [
      Math.min(start[0], cx), Math.min(start[1], cy),
      Math.max(start[0], cx), Math.max(start[1], cy)
    ];
    setRoi(newRoi);
    setDrawing(false);
    redraw(newRoi[0], newRoi[1], newRoi[2], newRoi[3]);
  };

  return (
    <div>
      <p className="text-muted" style={{ marginBottom: 8 }}>
        Draw the restricted zone for <strong>{cameraId}</strong>
      </p>
      <canvas
        ref={canvasRef}
        width={640} height={360}
        style={{ borderRadius: 8, cursor: "crosshair", display: "block", maxWidth: "100%" }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
      />
      {roi && (
        <div style={{ marginTop: 12, display: "flex", gap: 12, alignItems: "center" }}>
          <span className="text-muted">
            ROI: [{roi.join(", ")}]
          </span>
          <button className="btn btn-primary" onClick={() => onSave(roi)}>
            Save ROI
          </button>
        </div>
      )}
    </div>
  );
}