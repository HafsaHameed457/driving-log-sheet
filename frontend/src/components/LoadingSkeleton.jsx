export default function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="h-5 w-24 bg-slate-200 rounded mb-3" />
        <div className="h-[400px] bg-slate-100 rounded" />
      </div>
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="h-5 w-32 bg-slate-200 rounded mb-3" />
        <div className="h-[600px] bg-slate-100 rounded" />
      </div>
    </div>
  );
}
