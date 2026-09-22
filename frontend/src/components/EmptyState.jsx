export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="text-5xl mb-4">🚛</div>
      <h3 className="text-lg font-semibold text-navy-800 mb-1">
        Plan your first trip
      </h3>
      <p className="text-sm text-slate-500 max-w-sm">
        Enter your current, pickup, and dropoff locations on the left to see
        the route and generate FMCSA-compliant daily log sheets.
      </p>
    </div>
  );
}
