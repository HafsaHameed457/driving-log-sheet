import { useState } from "react";
import TripForm from "./components/TripForm";
import RouteMap from "./components/RouteMap";
import { planTrip } from "./api/client";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(payload) {
    setLoading(true);
    setError("");
    try {
      const data = await planTrip(payload);
      setResult(data);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="no-print flex items-center justify-between bg-navy-800 py-4 px-6">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded bg-amber-400" />
          <h1 className="text-xl font-bold text-white">Driving Log Sheet</h1>
        </div>
        <p className="text-sm text-slate-300 hidden md:block">
          Plan your route. Generate compliant ELD logs.
        </p>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div
            className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            role="alert"
          >
            {error}
          </div>
        )}

        <TripForm onSubmit={handleSubmit} loading={loading} />

        {result && (
          <div className="mt-6">
            <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
              <div>
                <span className="text-slate-500">Total miles:</span>{" "}
                <span className="font-semibold">
                  {Math.round(result.route.total_miles)}
                </span>
              </div>
              <div>
                <span className="text-slate-500">Drive hours:</span>{" "}
                <span className="font-semibold">
                  {result.route.total_drive_hrs.toFixed(1)}
                </span>
              </div>
              <div>
                <span className="text-slate-500">Stops:</span>{" "}
                <span className="font-semibold">{result.stops.length}</span>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
              <h2 className="text-lg font-semibold text-navy-800 mb-3">Route</h2>
              <RouteMap geometry={result.route.geometry} stops={result.stops} />
            </div>

            <details className="mt-4 text-sm">
              <summary className="cursor-pointer text-slate-600">
                Debug JSON
              </summary>
              <pre className="mt-2 overflow-auto rounded-md bg-slate-900 text-slate-100 p-3 text-xs">
                {JSON.stringify(result, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </main>
    </div>
  );
}
