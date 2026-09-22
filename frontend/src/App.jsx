export default function App() {
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
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">
          Form, map, and log sheets coming soon.
        </div>
      </main>
    </div>
  );
}
