const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const PHOTON_URL = "https://photon.komoot.io/api/";

function buildPhotonLabel(props, fallback) {
  if (props.label) return props.label;
  const parts = [props.name, props.city, props.state, props.country];
  const unique = parts.filter((p, i) => p && parts.indexOf(p) === i);
  return unique.length ? unique.join(", ") : fallback;
}

async function searchPhoton(q, signal) {
  const res = await fetch(
    `${PHOTON_URL}?q=${encodeURIComponent(q)}&limit=5`,
    { signal }
  );
  if (!res.ok) {
    throw new Error(`Photon request failed (${res.status})`);
  }
  const data = await res.json();
  return (data.features || []).map((f) => {
    const coords = (f.geometry && f.geometry.coordinates) || [];
    return {
      label: buildPhotonLabel(f.properties || {}, q),
      lat: coords[1],
      lng: coords[0],
    };
  });
}

async function searchBackend(q, signal) {
  const res = await fetch(
    `${BASE}/api/geocode/?q=${encodeURIComponent(q)}`,
    { signal }
  );
  if (!res.ok) {
    throw new Error(`Geocode request failed (${res.status})`);
  }
  return res.json();
}

export async function searchLocations(q, signal) {
  try {
    return await searchPhoton(q, signal);
  } catch (err) {
    if (err && err.name === "AbortError") throw err;
    return searchBackend(q, signal);
  }
}
