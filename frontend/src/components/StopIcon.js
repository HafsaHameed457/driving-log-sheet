import L from "leaflet";

export const STYLES = {
  pickup:  { color: "#10b981", glyph: "P" },
  dropoff: { color: "#ef4444", glyph: "D" },
  fuel:    { color: "#f59e0b", glyph: "F" },
  break:   { color: "#3b82f6", glyph: "B" },
  rest:    { color: "#8b5cf6", glyph: "R" },
  restart: { color: "#0f172a", glyph: "34" },
};

export function stopIcon(type) {
  const s = STYLES[type] || { color: "#64748b", glyph: "?" };
  return L.divIcon({
    className: "",
    html: `
      <div style="
        background:${s.color};
        width:28px;height:28px;border-radius:50%;
        border:2px solid white;
        box-shadow:0 1px 4px rgba(0,0,0,0.35);
        display:flex;align-items:center;justify-content:center;
        color:white;font-weight:700;font-size:12px;font-family:Inter,sans-serif;
      ">${s.glyph}</div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}
