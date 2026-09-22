import LogSheet from "./LogSheet";

export default function LogSheetList({ logs }) {
  if (!logs || logs.length === 0) return null;
  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-navy-800">Daily Logs</h2>
        <button
          onClick={() => window.print()}
          className="no-print text-sm px-3 py-1.5 rounded-md border border-slate-300 hover:bg-slate-100"
        >
          Print / Save PDF
        </button>
      </div>
      <div className="space-y-6">
        {logs.map((log, i) => (
          <LogSheet key={log.date} log={log} index={i} totalPages={logs.length} />
        ))}
      </div>
    </div>
  );
}
