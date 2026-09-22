import { STYLES as STOP_COLOR } from "./StopIcon.js";
import { formatArrive } from "../utils/format.js";

export default function TripSummary({ result }) {
  if (!result) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-navy-800 mb-4">Trip Summary</h2>

      <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
        <div>
          <div className="text-slate-500">Total miles</div>
          <div className="text-xl font-semibold text-navy-800">
            {Math.round(result.route.total_miles)}
          </div>
        </div>
        <div>
          <div className="text-slate-500">Drive hours</div>
          <div className="text-xl font-semibold text-navy-800">
            {result.route.total_drive_hrs.toFixed(1)}
          </div>
        </div>
        <div>
          <div className="text-slate-500">Total stops</div>
          <div className="text-xl font-semibold text-navy-800">
            {result.stops.length}
          </div>
        </div>
        <div>
          <div className="text-slate-500">Days</div>
          <div className="text-xl font-semibold text-navy-800">
            {result.logs.length}
          </div>
        </div>
      </div>

      <h3 className="text-sm font-semibold text-navy-800 mb-2">Stops</h3>
      <div>
        {result.stops.map((stop, i) => (
          <div
            key={i}
            className="flex items-start gap-3 py-2 border-b border-slate-100 last:border-0"
          >
            <span
              className="mt-1 inline-block w-2.5 h-2.5 rounded-full"
              style={{ background: STOP_COLOR[stop.type]?.color || "#64748b" }}
            />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-navy-800 capitalize">
                {stop.type}
              </div>
              <div className="text-xs text-slate-500 truncate">{stop.label}</div>
            </div>
            <div className="text-xs text-slate-400 whitespace-nowrap">
              {formatArrive(stop.arrive)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
