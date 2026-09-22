import { useState } from "react";
import TripForm from "./components/TripForm";
import RouteMap from "./components/RouteMap";
import TripSummary from "./components/TripSummary";
import EmptyState from "./components/EmptyState";
import LoadingSkeleton from "./components/LoadingSkeleton";
import { planTrip } from "./api/client";
import LogSheetList from "./components/LogSheetList";

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

      <main className="max-w-7xl mx-auto w-full flex-1 px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column: form + summary */}
          <div className="lg:col-span-1 space-y-6">
            {error && (
              <div
                className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                role="alert"
              >
                <div className="font-medium mb-1">Could not plan trip</div>
                <div>{error}</div>
              </div>
            )}
            <TripForm onSubmit={handleSubmit} loading={loading} />
            {result && <TripSummary result={result} />}
          </div>

          {/* Right column: map + logs */}
          <div className="lg:col-span-2 space-y-6">
            {loading ? (
              <LoadingSkeleton />
            ) : (
              <>
                {result && (
                  <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
                    <h2 className="text-lg font-semibold text-navy-800 mb-3">
                      Route
                    </h2>
                    <RouteMap
                      geometry={result.route.geometry}
                      stops={result.stops}
                    />
                  </div>
                )}
                {result && <LogSheetList logs={result.logs} />}
                {!result && !loading && <EmptyState />}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
