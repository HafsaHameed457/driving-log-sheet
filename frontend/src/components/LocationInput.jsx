import { useCallback, useEffect, useRef, useState } from "react";
import AsyncSelect from "react-select/async";
import { searchLocations } from "../utils/api";

const DEBOUNCE_MS = 300;

export default function LocationInput({
  label,
  value,
  onChange,
  placeholder,
  required,
}) {
  const [inputValue, setInputValue] = useState("");
  const [searchFailed, setSearchFailed] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const loadOptions = useCallback((text, callback) => {
    const query = text.trim();
    if (timerRef.current) clearTimeout(timerRef.current);
    if (query.length < 3) {
      setSearchFailed(false);
      callback([]);
      return;
    }
    timerRef.current = setTimeout(() => {
      searchLocations(query)
        .then((results) => {
          setSearchFailed(false);
          callback((results || []).map((r) => ({ label: r.label, value: r })));
        })
        .catch(() => {
          setSearchFailed(true);
          callback([]);
        });
    }, DEBOUNCE_MS);
  }, []);

  const selected = value
    ? { label: value, value: { label: value } }
    : null;

  function handleChange(option) {
    onChange(option ? option.label : "");
    setInputValue("");
  }

  function handleInputChange(val, meta) {
    if (meta.action !== "input-change") return;
    setInputValue(val);
  }

  // Block Enter from submitting form unless an option is selected
  function handleKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      e.stopPropagation();
    }
  }

  return (
    <div className="mb-4" onKeyDown={handleKeyDown}>
      <label className="block text-sm font-medium text-navy-700 mb-1">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>
      <AsyncSelect
        cacheOptions
        defaultOptions={false}
        loadOptions={loadOptions}
        inputValue={inputValue}
        onInputChange={handleInputChange}
        value={selected}
        onChange={handleChange}
        placeholder={placeholder}
        isClearable
        noOptionsMessage={({ inputValue: v }) => {
          if (searchFailed) {
            return "Location search is unavailable. Please try again.";
          }
          return v.trim().length < 3
            ? "Type at least 3 characters"
            : "No matching locations";
        }}
        loadingMessage={() => "Searching..."}
        styles={{
          control: (base, state) => ({
            ...base,
            minHeight: "42px",
            borderRadius: "0.375rem",
            borderColor: state.isFocused ? "#f59e0b" : "#cbd5e1",
            boxShadow: state.isFocused
              ? "0 0 0 2px rgba(245, 158, 11, 0.4)"
              : "none",
            "&:hover": { borderColor: "#f59e0b" },
          }),
          option: (base, state) => ({
            ...base,
            backgroundColor: state.isFocused ? "#fffbeb" : "white",
            color: "#0f172a",
            fontSize: "0.875rem",
          }),
          menu: (base) => ({
            ...base,
            borderRadius: "0.375rem",
            boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)",
            zIndex: 20,
          }),
        }}
      />
    </div>
  );
}
