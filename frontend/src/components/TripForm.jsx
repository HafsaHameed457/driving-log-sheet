import { useState } from "react";
import LocationInput from "./LocationInput";

const SAMPLE = {
  current_location: "Dallas, TX",
  pickup_location: "Oklahoma City, OK",
  dropoff_location: "Denver, CO",
  cycle_used_hrs: "22.5",
};

export default function TripForm({ onSubmit, loading }) {
  const [current_location, setCurrentLocation] = useState("");
  const [pickup_location, setPickupLocation] = useState("");
  const [dropoff_location, setDropoffLocation] = useState("");
  const [cycle_used_hrs, setCycleUsedHrs] = useState("");
  const [error, setError] = useState("");

  function fillSample() {
    setCurrentLocation(SAMPLE.current_location);
    setPickupLocation(SAMPLE.pickup_location);
    setDropoffLocation(SAMPLE.dropoff_location);
    setCycleUsedHrs(SAMPLE.cycle_used_hrs);
    setError("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const cur = current_location.trim();
    const pick = pickup_location.trim();
    const drop = dropoff_location.trim();

    if (!cur) {
      setError("Please select a current location from the suggestions.");
      return;
    }
    if (!pick) {
      setError("Please select a pickup location from the suggestions.");
      return;
    }
    if (!drop) {
      setError("Please select a dropoff location from the suggestions.");
      return;
    }

    const cycle = parseFloat(cycle_used_hrs);
    if (
      cycle_used_hrs.trim() === "" ||
      Number.isNaN(cycle) ||
      cycle < 0 ||
      cycle > 70
    ) {
      setError("Cycle used must be a number between 0 and 70.");
      return;
    }

    if (pick.toLowerCase() === drop.toLowerCase()) {
      setError("Pickup and dropoff cannot be the same location.");
      return;
    }

    setError("");

    try {
      await onSubmit({
        current_location: cur,
        pickup_location: pick,
        dropoff_location: drop,
        cycle_used_hrs: cycle,
      });
    } catch {
      // App surfaces network errors above the form card.
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-navy-800 mb-4">Trip Details</h2>

      {error && (
        <div
          className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          role="alert"
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <LocationInput
          id="current-location"
          label="Current Location"
          value={current_location}
          onChange={setCurrentLocation}
          placeholder="e.g. Dallas, TX"
          required
        />
        <LocationInput
          id="pickup-location"
          label="Pickup Location"
          value={pickup_location}
          onChange={setPickupLocation}
          placeholder="e.g. Oklahoma City, OK"
          required
        />
        <LocationInput
          id="dropoff-location"
          label="Dropoff Location"
          value={dropoff_location}
          onChange={setDropoffLocation}
          placeholder="e.g. Denver, CO"
          required
        />

        <div className="mb-4">
          <label
            htmlFor="cycle-used-hrs"
            className="block text-sm font-medium text-navy-700 mb-1"
          >
            Current Cycle Used (hrs)<span className="text-red-500"> *</span>
          </label>
          <input
            id="cycle-used-hrs"
            type="number"
            value={cycle_used_hrs}
            onChange={(e) => setCycleUsedHrs(e.target.value)}
            placeholder="e.g. 22.5"
            min={0}
            max={70}
            step={0.5}
            className="w-full rounded-md border border-slate-300 px-3 py-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus:border-amber-500"
          />
        </div>

        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={loading}
            className="bg-amber-500 hover:bg-amber-600 text-navy-900 font-semibold py-2.5 px-6 rounded-md disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
          >
            {loading && (
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-navy-900 border-t-transparent" />
            )}
            {loading ? "Planning..." : "Plan Trip"}
          </button>

          <button
            type="button"
            onClick={fillSample}
            className="text-navy-700 underline hover:text-amber-600 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 rounded px-1"
          >
            Try sample trip
          </button>
        </div>
      </form>
    </div>
  );
}
