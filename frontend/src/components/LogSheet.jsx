const W = 1200;
const H = 720;
const TIME_LEFT = 200;
const TIME_RIGHT = 1100;
const GRID_TOP = 220;
const ROW_HEIGHT = 55;
const ROW_GAP = 6;
const TOTAL_X = 1110;
const TOTAL_W = 80;

const MINUTES_IN_DAY = 1440;
const timeToX = (hhmm) => {
  const [h, m] = hhmm.split(":").map(Number);
  return TIME_LEFT + ((h * 60 + m) / MINUTES_IN_DAY) * (TIME_RIGHT - TIME_LEFT);
};
const STATUS_TO_ROW = { off_duty: 0, sleeper: 1, driving: 2, on_duty: 3 };
const rowY = (status) => GRID_TOP + STATUS_TO_ROW[status] * (ROW_HEIGHT + ROW_GAP);
const rowCenterY = (status) => rowY(status) + ROW_HEIGHT / 2;

const ROW_FILL = {
  off_duty: "#ffffff",
  sleeper: "#f8fafc",
  driving: "#fff7ed",
  on_duty: "#eff6ff",
};

const ROW_ORDER = ["off_duty", "sleeper", "driving", "on_duty"];
const ROW_LABELS = {
  off_duty: "1. Off Duty",
  sleeper: "2. Sleeper Berth",
  driving: "3. Driving",
  on_duty: "4. On Duty (not driving)",
};

const GRID_BOTTOM = GRID_TOP + 4 * (ROW_HEIGHT + ROW_GAP) - ROW_GAP;

export default function LogSheet({ log, index, totalPages }) {
  const [year, month, day] = log.date.split("-");

  function renderHeader() {
    return (
      <g>
        <text x={20} y={18} fontSize={11} fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          [24-hour]
        </text>
        <text x={W - 20} y={18} fontSize={11} textAnchor="end" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Original - File at home terminal
        </text>
        <text x={W - 20} y={32} fontSize={8} textAnchor="end" fontFamily="Inter, system-ui, sans-serif" fill="#64748b">
          Duplicate - Driver retains current copy and surrenders to carrier within 13 days
        </text>

        <text x={20} y={50} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Month
        </text>
        <rect x={60} y={36} width={50} height={20} fill="#ffffff" stroke="#94a3b8" strokeWidth={0.7} />
        <text x={85} y={50} fontSize={11} textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {month}
        </text>
        <text x={120} y={50} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Day
        </text>
        <rect x={150} y={36} width={50} height={20} fill="#ffffff" stroke="#94a3b8" strokeWidth={0.7} />
        <text x={175} y={50} fontSize={11} textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {day}
        </text>
        <text x={210} y={50} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Year
        </text>
        <rect x={245} y={36} width={60} height={20} fill="#ffffff" stroke="#94a3b8" strokeWidth={0.7} />
        <text x={275} y={50} fontSize={11} textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {year}
        </text>

        <text x={340} y={50} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          From: {log.from_location}
        </text>
        <text x={560} y={50} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          To: {log.to_location}
        </text>

        <line x1={20} y1={62} x2={W - 20} y2={62} stroke="#94a3b8" strokeWidth={0.5} />

        <text x={20} y={82} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Total Miles Driving Today: {log.total_miles_today}
        </text>
        <text x={340} y={82} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Total Mileage Today: {log.total_miles_today}
        </text>

        <line x1={20} y1={94} x2={W - 20} y2={94} stroke="#94a3b8" strokeWidth={0.5} />

        <text x={20} y={114} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Name of Carrier: ______
        </text>
        <text x={440} y={114} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Main Office Address: ______
        </text>

        <line x1={20} y1={126} x2={W - 20} y2={126} stroke="#94a3b8" strokeWidth={0.5} />

        <text x={20} y={146} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Truck/Trailer Numbers: ______
        </text>
        <text x={440} y={146} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Home Terminal Address: ______
        </text>

        <line x1={20} y1={158} x2={W - 20} y2={158} stroke="#94a3b8" strokeWidth={0.5} />

        <text x={20} y={178} fontSize={11} fontFamily="Inter, system-ui, sans-serif" fill="#64748b">
         (driver signature area)
        </text>
        <line x1={20} y1={196} x2={W - 20} y2={196} stroke="#94a3b8" strokeWidth={0.5} />
      </g>
    );
  }

  function renderGrid() {
    const hourLabelsLeft = [];
    for (let h = 1; h <= 11; h++) {
      const x = TIME_LEFT + (h / 24) * (TIME_RIGHT - TIME_LEFT);
      hourLabelsLeft.push(
        <text key={`hl-${h}`} x={x} y={GRID_TOP - 12} fontSize={9} textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {h}
        </text>
      );
    }
    const hourLabelsRight = [];
    for (let h = 13; h <= 23; h++) {
      const x = TIME_LEFT + (h / 24) * (TIME_RIGHT - TIME_LEFT);
      hourLabelsRight.push(
        <text key={`hr-${h}`} x={x} y={GRID_TOP - 12} fontSize={9} textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {h - 12}
        </text>
      );
    }

    const gridlines = [];
    for (let minute = 0; minute < MINUTES_IN_DAY; minute += 15) {
      const x = TIME_LEFT + (minute / MINUTES_IN_DAY) * (TIME_RIGHT - TIME_LEFT);
      const isHour = minute % 60 === 0;
      gridlines.push(
        <line
          key={`gl-${minute}`}
          x1={x}
          y1={GRID_TOP}
          x2={x}
          y2={GRID_BOTTOM}
          stroke={isHour ? "#94a3b8" : "#cbd5e1"}
          strokeWidth={isHour ? 0.6 : 0.3}
        />
      );
    }

    const dutySegments = [];
    const dutyConnectors = [];
    log.events.forEach((event, i) => {
      const x1 = timeToX(event.start);
      const x2 = timeToX(event.end);
      const y = rowCenterY(event.status);
      dutySegments.push(
        <g key={`seg-${i}`}>
          <line x1={x1} y1={y} x2={x2} y2={y} stroke="#0f172a" strokeWidth={2.5} strokeLinecap="round" />
          <circle cx={x1} cy={y} r={2.5} fill="#0f172a" />
          <circle cx={x2} cy={y} r={2.5} fill="#0f172a" />
        </g>
      );
      const next = log.events[i + 1];
      if (next && next.status !== event.status) {
        const x = timeToX(event.end);
        const y1 = rowCenterY(event.status);
        const y2 = rowCenterY(next.status);
        dutyConnectors.push(
          <line
            key={`conn-${i}`}
            x1={x}
            y1={y1}
            x2={x}
            y2={y2}
            stroke="#0f172a"
            strokeWidth={1.5}
            strokeDasharray="3 3"
          />
        );
      }
    });

    const totalBoxes = ROW_ORDER.map((status) => (
      <g key={`tot-${status}`}>
        <rect
          x={TOTAL_X}
          y={rowY(status)}
          width={TOTAL_W}
          height={ROW_HEIGHT}
          fill="#ffffff"
          stroke="#94a3b8"
          strokeWidth={0.7}
        />
        <text
          x={TOTAL_X + TOTAL_W / 2}
          y={rowCenterY(status) + 4}
          fontSize={11}
          textAnchor="middle"
          fontWeight={600}
          fontFamily="Inter, system-ui, sans-serif"
          fill="#0f172a"
        >
          {log.totals[status].toFixed(2)}
        </text>
      </g>
    ));

    return (
      <g>
        {ROW_ORDER.map((status) => (
          <rect
            key={`bg-${status}`}
            x={TIME_LEFT}
            y={rowY(status)}
            width={TIME_RIGHT - TIME_LEFT}
            height={ROW_HEIGHT}
            fill={ROW_FILL[status]}
            stroke="#94a3b8"
            strokeWidth={0.7}
          />
        ))}

        {ROW_ORDER.map((status) => (
          <text
            key={`lbl-${status}`}
            x={30}
            y={rowCenterY(status) + 4}
            fontSize={11}
            fontWeight={600}
            fontFamily="Inter, system-ui, sans-serif"
            fill="#0f172a"
          >
            {ROW_LABELS[status]}
          </text>
        ))}

        <text x={TIME_LEFT + 2} y={GRID_TOP - 12} fontSize={9} textAnchor="start" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Mid-night
        </text>
        {hourLabelsLeft}
        <text
          x={TIME_LEFT + (12 / 24) * (TIME_RIGHT - TIME_LEFT)}
          y={GRID_TOP - 12}
          fontSize={9}
          textAnchor="middle"
          fontFamily="Inter, system-ui, sans-serif"
          fill="#0f172a"
        >
          Noon
        </text>
        {hourLabelsRight}
        <text x={TIME_RIGHT - 2} y={GRID_TOP - 12} fontSize={9} textAnchor="end" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Mid-night
        </text>

        <text x={TIME_LEFT} y={GRID_TOP - 25} fontSize={9} fill="#64748b" fontFamily="Inter, system-ui, sans-serif">
          Complete this grid in ink.
        </text>
        <text x={TOTAL_X + TOTAL_W / 2} y={GRID_TOP - 25} fontSize={10} textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Total Hours
        </text>

        {gridlines}
        {dutySegments}
        {dutyConnectors}
        {totalBoxes}
      </g>
    );
  }

  function renderRemarks() {
    const ruleY = GRID_TOP + 4 * (ROW_HEIGHT + ROW_GAP) + 10;
    const yBase = GRID_TOP + 4 * (ROW_HEIGHT + ROW_GAP) + 40;

    const remarks = [];
    log.events.forEach((event, i) => {
      if (i === 0 || event.status !== log.events[i - 1].status) {
        const x = timeToX(event.start);
        const yOffset = (i % 2) * 60;
        const y = yBase + yOffset;
        remarks.push(
          <text
            key={`rem-${i}`}
            x={x}
            y={y}
            fontSize={9}
            fill="#0f172a"
            transform={`rotate(-90 ${x} ${y})`}
            textAnchor="start"
            fontFamily="Inter, system-ui, sans-serif"
          >
            <tspan x={x} dy={0}>
              {event.location}
            </tspan>
            <tspan x={x} dy={12}>
              {event.remark}
            </tspan>
          </text>
        );
      }
    });

    return (
      <g>
        <line x1={20} y1={ruleY} x2={TIME_RIGHT} y2={ruleY} stroke="#94a3b8" strokeWidth={0.5} />
        <text x={30} y={ruleY + 15} fontSize={11} fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Remarks
        </text>
        {remarks}
      </g>
    );
  }

  function renderRecap() {
    const x = 780;
    const y = 620;
    const w = 410;
    const h = 80;
    const colA = x + 250;
    const colB = x + 300;
    const colC = x + 350;
    const rowH = 20;

    return (
      <g>
        <text x={x} y={y - 6} fontSize={10} fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          70 Hour / 8 Day
        </text>
        <rect x={x} y={y} width={w} height={h} fill="#ffffff" stroke="#94a3b8" strokeWidth={0.7} />
        <line x1={x} y1={y + rowH} x2={x + w} y2={y + rowH} stroke="#94a3b8" strokeWidth={0.5} />
        <line x1={colA} y1={y} x2={colA} y2={y + h} stroke="#94a3b8" strokeWidth={0.5} />
        <line x1={colB} y1={y} x2={colB} y2={y + h} stroke="#94a3b8" strokeWidth={0.5} />
        <line x1={colC} y1={y} x2={colC} y2={y + h} stroke="#94a3b8" strokeWidth={0.5} />
        <line x1={x} y1={y + 2 * rowH} x2={x + w} y2={y + 2 * rowH} stroke="#94a3b8" strokeWidth={0.5} />
        <line x1={x} y1={y + 3 * rowH} x2={x + w} y2={y + 3 * rowH} stroke="#94a3b8" strokeWidth={0.5} />

        <text x={(x + colA) / 2} y={y + 14} fontSize={9} textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Description
        </text>
        <text x={(colA + colB) / 2} y={y + 14} fontSize={9} textAnchor="middle" fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          A
        </text>
        <text x={(colB + colC) / 2} y={y + 14} fontSize={9} textAnchor="middle" fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          B
        </text>
        <text x={(colC + x + w) / 2} y={y + 14} fontSize={9} textAnchor="middle" fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          C
        </text>

        <text x={x + 6} y={y + rowH + 14} fontSize={9} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          On duty today, total lines 3 &amp; 4
        </text>
        <text x={(colA + colB) / 2} y={y + rowH + 14} fontSize={11} textAnchor="middle" fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {log.recap.on_duty_today.toFixed(2)}
        </text>

        <text x={x + 6} y={y + 2 * rowH + 14} fontSize={9} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Total hours on duty last 7 days incl. today
        </text>
        <text x={(colB + colC) / 2} y={y + 2 * rowH + 14} fontSize={11} textAnchor="middle" fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {log.recap.total_70hr.toFixed(2)}
        </text>

        <text x={x + 6} y={y + 3 * rowH + 14} fontSize={9} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          Total hours available tomorrow 70 hr minus A
        </text>
        <text x={(colC + x + w) / 2} y={y + 3 * rowH + 14} fontSize={11} textAnchor="middle" fontWeight={600} fontFamily="Inter, system-ui, sans-serif" fill="#0f172a">
          {log.recap.available_tomorrow.toFixed(2)}
        </text>
      </g>
    );
  }

  return (
    <section className="log-sheet bg-white rounded-lg border border-slate-300 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-100 border-b border-slate-300">
        <span className="text-sm font-semibold text-navy-800">
          Driver's Daily Log — {log.date}
        </span>
        <span className="text-xs text-slate-500">
          Page {index + 1} of {totalPages}
        </span>
      </div>
      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full min-w-[900px] block"
          role="img"
          aria-label={`Driver's daily log for ${log.date}`}
        >
          <title>{`Driver's daily log for ${log.date}`}</title>
          {renderHeader()}
          {renderGrid()}
          {renderRemarks()}
          {renderRecap()}
        </svg>
      </div>
    </section>
  );
}
