import { useState } from "react";
import TripForm from "./components/TripForm";
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
          <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-semibold text-navy-800 mb-2">
              Plan result (temporary JSON dump)
            </h3>
            <pre className="text-xs overflow-auto max-h-96 bg-slate-50 rounded p-3">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </main>
    </div>
  );
}
