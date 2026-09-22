const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function searchLocations(q, signal) {
  const res = await fetch(
    `${BASE}/api/geocode/?q=${encodeURIComponent(q)}`,
    { signal }
  );
  if (!res.ok) {
    throw new Error(`Geocode request failed (${res.status})`);
  }
  return res.json();
}
