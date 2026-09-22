import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 60000,
});

// Normalize error messages so the UI never shows a raw stack trace.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err?.response?.data?.error ||
      err?.response?.data?.detail ||
      err?.message ||
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(msg));
  }
);

export async function planTrip(payload) {
  const { data } = await api.post("/api/trip/", payload);
  return data;
}

export default api;
