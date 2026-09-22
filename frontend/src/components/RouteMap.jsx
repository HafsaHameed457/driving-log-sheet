import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const STOP_META = {
  pickup: { color: "#16a34a", label: "Pickup" },
  dropoff: { color: "#dc2626", label: "Dropoff" },
  fuel: { color: "#2563eb", label: "Fuel" },
  break: { color: "#f59e0b", label: "Break" },
  rest: { color: "#7c3aed", label: "Rest" },
  restart: { color: "#0ea5e9", label: "Restart" },
};

function makeIcon(hex) {
  return L.divIcon({
    className: "",
    html: `<span style="display:block;width:14px;height:14px;border-radius:9999px;background:${hex};border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.45)"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

function formatArrive(iso) {
  if (!iso) return "";
  const [datePart, timePart] = iso.split("T");
  if (!datePart || !timePart) return iso;
  const [, m, d] = datePart.split("-").map(Number);
  const [hh, mm] = timePart.split(":").map(Number);
  const ampm = hh >= 12 ? "PM" : "AM";
  const h12 = hh % 12 || 12;
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[m - 1]} ${d}, ${h12}:${String(mm).padStart(2, "0")} ${ampm}`;
}

function formatDuration(min) {
  if (min == null) return "";
  if (min >= 60) {
    const h = Math.floor(min / 60);
    const m = min % 60;
    return m ? `${h}h ${m}m` : `${h}h`;
  }
  return `${min} min`;
}

function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) map.fitBounds(bounds, { padding: [30, 30] });
  }, [map, bounds]);
  return null;
}

export default function RouteMap({ geometry, stops = [] }) {
  const positions = useMemo(
    () => (Array.isArray(geometry) ? geometry.filter((p) => Array.isArray(p) && p.length === 2) : []),
    [geometry]
  );

  const bounds = useMemo(
    () => (positions.length ? L.latLngBounds(positions) : null),
    [positions]
  );

  if (!positions.length) {
    return (
      <div className="flex h-96 items-center justify-center rounded-lg border border-slate-200 bg-white text-sm text-slate-500">
        No route geometry to display.
      </div>
    );
  }

  return (
    <div className="relative h-96 overflow-hidden rounded-lg border border-slate-200">
      <MapContainer
        bounds={bounds}
        boundsOptions={{ padding: [30, 30] }}
        className="h-full w-full"
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds bounds={bounds} />
        <Polyline
          positions={positions}
          pathOptions={{ color: "#f59e0b", weight: 4, opacity: 0.9 }}
        />
        {stops.map((stop, i) => {
          const meta = STOP_META[stop.type] || { color: "#0f172a", label: stop.type };
          if (typeof stop.lat !== "number" || typeof stop.lng !== "number") return null;
          return (
            <Marker
              key={`${stop.type}-${i}-${stop.lat}-${stop.lng}`}
              position={[stop.lat, stop.lng]}
              icon={makeIcon(meta.color)}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold" style={{ color: meta.color }}>
                    {meta.label}
                  </div>
                  <div>{stop.label}</div>
                  <div className="text-slate-600">
                    Arrive {formatArrive(stop.arrive)}
                    {stop.duration_min ? ` · ${formatDuration(stop.duration_min)}` : ""}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      <div className="pointer-events-none absolute bottom-2 left-2 z-[1000] rounded-md border border-slate-200 bg-white/95 px-3 py-2 shadow">
        <div className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-navy-700">
          Legend
        </div>
        <ul className="space-y-1">
          {Object.entries(STOP_META).map(([type, meta]) => (
            <li key={type} className="flex items-center gap-2 text-xs text-navy-800">
              <span
                className="inline-block h-2.5 w-2.5 rounded-full border border-white"
                style={{ background: meta.color, boxShadow: "0 0 0 1px rgba(0,0,0,.15)" }}
              />
              {meta.label}
            </li>
          ))}
        </ul>
        <div className="mt-1.5 flex items-center gap-2 text-xs text-navy-800">
          <span className="inline-block h-0.5 w-6 rounded" style={{ background: "#f59e0b" }} />
          Route
        </div>
      </div>
    </div>
  );
}
