import { useEffect, useRef, useState } from "react";
import { searchLocations } from "../utils/api";

export default function LocationInput({
  label,
  value,
  onChange,
  placeholder,
  required,
}) {
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [searching, setSearching] = useState(false);
  const containerRef = useRef(null);
  const abortRef = useRef(null);

  // Debounced autocomplete (300ms, min 3 chars)
  useEffect(() => {
    const query = value.trim();

    if (query.length < 3) {
      setSuggestions([]);
      setOpen(false);
      setSearching(false);
      return undefined;
    }

    const timer = setTimeout(async () => {
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setSearching(true);
      try {
        const results = await searchLocations(query, controller.signal);
        if (abortRef.current !== controller) return;
        setSuggestions((results || []).slice(0, 5));
        setOpen(true);
        setSearching(false);
      } catch (err) {
        if (err.name === "AbortError") return;
        setSuggestions([]);
        setOpen(false);
        setSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [value]);

  // Abort in-flight request on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleSelect(labelText) {
    onChange(labelText);
    setOpen(false);
  }

  function handleKeyDown(e) {
    if (e.key === "Escape") setOpen(false);
  }

  return (
    <div className="relative mb-4" ref={containerRef} onKeyDown={handleKeyDown}>
      <label className="block text-sm font-medium text-navy-700 mb-1">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          className="w-full rounded-md border border-slate-300 px-3 py-2 pr-20 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
        />
        {searching && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 pointer-events-none">
            Searching...
          </span>
        )}
      </div>
      {open && suggestions.length > 0 && (
        <ul className="absolute z-10 left-0 right-0 mt-1 rounded-md border border-slate-200 bg-white shadow-lg max-h-60 overflow-auto">
          {suggestions.map((s, i) => (
            <li
              key={i}
              className="cursor-pointer px-3 py-2 text-sm text-navy-800 hover:bg-amber-50"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => handleSelect(s.label)}
            >
              {s.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
