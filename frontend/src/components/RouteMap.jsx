import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "../utils/leafletIcons.js";
import { stopIcon, STYLES } from "./StopIcon.js";
import { formatArrive } from "../utils/format.js";

function FitBounds({ geometry }) {
  const map = useMap();

  useEffect(() => {
    if (!geometry || geometry.length === 0) return;
    const bounds = L.latLngBounds(geometry.map(([lat, lng]) => [lat, lng]));
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [geometry, map]);

  useEffect(() => {
    const container = map.getContainer();
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(container);
    return () => observer.disconnect();
  }, [map]);

  return null;
}

export default function RouteMap({ geometry, stops = [] }) {
  if (!geometry || !Array.isArray(geometry) || geometry.length < 2) {
    return (
      <div className="h-[500px] flex items-center justify-center bg-slate-100 rounded-lg text-slate-500">
        No route to display.
      </div>
    );
  }

  return (
    <>
      <MapContainer
        center={[geometry[0][0], geometry[0][1]]}
        zoom={6}
        scrollWheelZoom={true}
        style={{ height: "500px", width: "100%" }}
        className="rounded-lg overflow-hidden border border-slate-200"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <Polyline
          positions={geometry}
          pathOptions={{ color: "#f59e0b", weight: 4, opacity: 0.85 }}
        />
        {stops.map((stop, i) => (
          <Marker
            key={i}
            position={[stop.lat, stop.lng]}
            icon={stopIcon(stop.type)}
          >
            <Popup>
              <div className="text-sm">
                <div className="font-semibold capitalize text-navy-800">
                  {stop.type}
                </div>
                <div className="text-slate-600">{stop.label}</div>
                <div className="text-slate-500 text-xs mt-1">
                  Arrive: {formatArrive(stop.arrive)}
                </div>
                <div className="text-slate-500 text-xs">
                  Duration: {stop.duration_min} min
                </div>
                <div className="text-slate-500 text-xs">
                  Mile {Math.round(stop.miles_from_start)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
        <FitBounds geometry={geometry} />
      </MapContainer>

      <div className="flex flex-wrap gap-3 mt-3 text-xs text-slate-600">
        {Object.entries(STYLES).map(([type, { color }]) => (
          <div key={type} className="flex items-center gap-1.5">
            <span
              className="inline-block w-3 h-3 rounded-full border border-white shadow"
              style={{ background: color }}
            />
            <span className="capitalize">{type}</span>
          </div>
        ))}
      </div>
    </>
  );
}
