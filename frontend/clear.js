const DATA = {
  latest: "../evidence/latest_run.json",
  suite: "../evidence/suite_report.json",
  extreme: "../evidence/extreme_batch_report.json",
  cctv: "../evidence/cctv_bmd45_report.json",
  route: "../data/orr_silk_board_whitefield_route_osrm.geojson",
  official: "../data/official_reference_bengaluru_cmp_2020.json"
};

const fmt = new Intl.NumberFormat("en-IN");
const pct = value => `${Math.round(Number(value || 0) * 100)}%`;
const km = metres => `${(Number(metres || 0) / 1000).toFixed(1)} km`;
const q = selector => document.querySelector(selector);
const setText = (selector, value) => {
  const node = q(selector);
  if (node) node.textContent = value;
};

async function loadJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  const text = await response.text();
  return JSON.parse(text.replace(/^\uFEFF/, ""));
}

function findAssertion(report, name) {
  return (report.assertions || []).find(item => item.name === name) || { details: {} };
}

function label(id, fallback = "checkpoint") {
  return String(id || fallback)
    .replace(/_/g, " ")
    .replace(/\b\w/g, char => char.toUpperCase());
}

function chooseDecision(latest, extreme) {
  const cycles = latest.cycles || [];
  const activatedCycle = cycles.find(cycle => (cycle.decisions || []).some(decision => decision.activate)) || cycles[cycles.length - 1] || {};
  const cycleDecision = (activatedCycle.decisions || []).find(decision => decision.activate) || (activatedCycle.decisions || [])[0];
  const aggregateDecision = ((extreme.aggregate_decisions || [])[0] || {}).decision;
  const decision = cycleDecision || aggregateDecision || {};
  return {
    cycle: activatedCycle,
    decision,
    checkpoint: activatedCycle.observation?.junction_id || "marathahalli",
    destination: activatedCycle.best_destination_id || decision.destination_id || "whitefield",
    confidence: activatedCycle.best_confidence || decision.confidence || 0,
    activate: Boolean(decision.activate)
  };
}

function renderNumbers({ latest, suite, extreme, cctv, route, official }) {
  const chosen = chooseDecision(latest, extreme);
  const stress = extreme.metrics || {};
  const images = findAssertion(cctv, "metadata_rows_match_coco_images").details.coco_images || 0;
  const annotations = findAssertion(cctv, "coco_annotations_present").details.annotation_count || 0;
  const silkBoard = (official.junction_counts || []).find(item => item.name === "Silk Board Junction") || {};
  const doddanakundi = (official.junction_counts || []).find(item => item.name === "Doddanakundi Junction") || {};

  const confidenceText = pct(chosen.confidence);
  const routePointText = fmt.format(route.coordinate_count || 0);
  setText("#route-distance", `${km(route.distance_m)} / ${routePointText} route points`);
  setText("#belief-percent", confidenceText);
  setText("#belief-destination", label(chosen.destination));
  const bar = q("#belief-bar");
  if (bar) bar.style.width = `${Math.max(0, Math.min(100, Math.round(Number(chosen.confidence || 0) * 100)))}%`;
  setText(
    "#hero-action",
    chosen.activate
      ? `At ${label(chosen.checkpoint)}, PTIS increases confidence toward ${label(chosen.destination)} based on continued route movement.`
      : `At ${label(chosen.checkpoint)}, PTIS keeps the capacity gate on standby.`
  );
  setText("#route-points-metric", routePointText);
  setText("#events-metric", fmt.format(stress.observation_count || 0));
  setText("#confidence-metric", confidenceText);
  setText("#safety-metric", fmt.format(stress.capacity_violation_count || 0));
  const calibrationError = Number(stress.mean_synthetic_od_abs_rate_error || 0) * 100;
  setText("#synthetic-calibration", `Synthetic OD calibration rate error: ${calibrationError.toFixed(2)}% in stress replay. This is synthetic calibration, not field OD accuracy.`);
  setText("#suite-pass", `${fmt.format(suite.passed_count || 0)}/${fmt.format(suite.scenario_count || 0)}`);
  setText("#stress-load", fmt.format(stress.vehicle_count || 0));
  setText("#observation-count", fmt.format(stress.observation_count || 0));
  setText("#safety-count", fmt.format(stress.capacity_violation_count || 0));
  setText("#cctv-count", `${fmt.format(images)} / ${fmt.format(annotations)}`);
  setText("#official-count", `${fmt.format(silkBoard.peak_hour_pcu || 0)} / ${fmt.format(doddanakundi.peak_hour_pcu || 0)} PCU`);
}

function routeCoordinates(route) {
  return (((route.features || [])[0] || {}).geometry || {}).coordinates || [];
}

function boundsFor(coords, waypoints) {
  const all = coords.concat((waypoints || []).map(point => [Number(point.lon), Number(point.lat)]));
  const lons = all.map(point => Number(point[0]));
  const lats = all.map(point => Number(point[1]));
  return {
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats)
  };
}

function renderFallback(route, latest, extreme) {
  const svg = q("#fallback-map");
  const coords = routeCoordinates(route);
  if (!svg || coords.length === 0) return;

  const chosen = chooseDecision(latest, extreme);
  const width = 980;
  const height = 620;
  const pad = 64;
  const bounds = boundsFor(coords, route.waypoints || []);
  const scaleX = (width - pad * 2) / Math.max(0.000001, bounds.maxLon - bounds.minLon);
  const scaleY = (height - pad * 2) / Math.max(0.000001, bounds.maxLat - bounds.minLat);
  const scale = Math.min(scaleX, scaleY);
  const offsetX = (width - (bounds.maxLon - bounds.minLon) * scale) / 2;
  const offsetY = (height - (bounds.maxLat - bounds.minLat) * scale) / 2;

  const project = coord => {
    const lon = Number(Array.isArray(coord) ? coord[0] : coord.lon);
    const lat = Number(Array.isArray(coord) ? coord[1] : coord.lat);
    return {
      x: offsetX + (lon - bounds.minLon) * scale,
      y: height - offsetY - (lat - bounds.minLat) * scale
    };
  };
  const d = coords.map((coord, index) => {
    const point = project(coord);
    return `${index === 0 ? "M" : "L"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
  }).join(" ");
  const nodes = (route.waypoints || []).map(point => {
    const projected = project(point);
    const className = ["fallback-node"];
    if (point.id === chosen.checkpoint) className.push("active");
    if (point.id === chosen.destination) className.push("target");
    const anchor = point.order > 4 ? "end" : "start";
    const dx = anchor === "end" ? -12 : 12;
    return `
      <circle class="${className.join(" ")}" cx="${projected.x.toFixed(1)}" cy="${projected.y.toFixed(1)}" r="8"></circle>
      <text class="fallback-label" x="${(projected.x + dx).toFixed(1)}" y="${(projected.y - 12).toFixed(1)}" text-anchor="${anchor}">${point.name}</text>
    `;
  }).join("");

  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.innerHTML = `
    <path class="fallback-route-shadow" d="${d}"></path>
    <path class="fallback-route-line" d="${d}"></path>
    ${nodes}
  `;
}

function initMapLibre(route, latest, extreme) {
  const frame = q(".map-frame");
  const coords = routeCoordinates(route);
  if (!frame || !window.maplibregl || coords.length === 0) return;

  const chosen = chooseDecision(latest, extreme);
  const routeGeoJson = {
    type: "FeatureCollection",
    features: [{
      type: "Feature",
      properties: { name: "Silk Board to Whitefield" },
      geometry: { type: "LineString", coordinates: coords }
    }]
  };
  const pointGeoJson = {
    type: "FeatureCollection",
    features: (route.waypoints || []).map(point => ({
      type: "Feature",
      properties: {
        id: point.id,
        name: point.name,
        state: point.id === chosen.destination ? "target" : (point.id === chosen.checkpoint ? "checkpoint" : "route")
      },
      geometry: { type: "Point", coordinates: [Number(point.lon), Number(point.lat)] }
    }))
  };
  const bounds = boundsFor(coords, route.waypoints || []);

  const map = new maplibregl.Map({
    container: "map",
    style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    center: [(bounds.minLon + bounds.maxLon) / 2, (bounds.minLat + bounds.maxLat) / 2],
    zoom: 10.7,
    pitch: 0,
    bearing: 0,
    attributionControl: true
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.dragRotate.disable();
  map.touchZoomRotate.disableRotation();

  map.on("load", () => {
    map.addSource("ptis-route", { type: "geojson", data: routeGeoJson });
    map.addLayer({
      id: "ptis-route-shadow",
      type: "line",
      source: "ptis-route",
      paint: { "line-color": "#0f172a", "line-width": 13, "line-opacity": .18, "line-blur": 1.4 }
    });
    map.addLayer({
      id: "ptis-route-line",
      type: "line",
      source: "ptis-route",
      paint: { "line-color": "#13c8bd", "line-width": 6, "line-opacity": .98 }
    });
    map.addSource("ptis-points", { type: "geojson", data: pointGeoJson });
    map.addLayer({
      id: "ptis-point-halo",
      type: "circle",
      source: "ptis-points",
      paint: {
        "circle-radius": ["match", ["get", "state"], "target", 18, "checkpoint", 16, 11],
        "circle-color": "#ffffff",
        "circle-opacity": .95,
        "circle-stroke-color": "#cbd5e1",
        "circle-stroke-width": 1
      }
    });
    map.addLayer({
      id: "ptis-point-dot",
      type: "circle",
      source: "ptis-points",
      paint: {
        "circle-radius": ["match", ["get", "state"], "target", 10, "checkpoint", 9, 6],
        "circle-color": ["match", ["get", "state"], "target", "#13c8bd", "checkpoint", "#13c8bd", "#071739"],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 2
      }
    });
    map.addLayer({
      id: "ptis-point-label",
      type: "symbol",
      source: "ptis-points",
      layout: {
        "text-field": ["get", "name"],
        "text-size": 12,
        "text-offset": [0, 1.8],
        "text-anchor": "top",
        "text-allow-overlap": false
      },
      paint: { "text-color": "#0f172a", "text-halo-color": "#ffffff", "text-halo-width": 1.5 }
    });
    map.fitBounds([[bounds.minLon, bounds.minLat], [bounds.maxLon, bounds.maxLat]], {
      padding: { top: 74, right: 62, bottom: 98, left: 62 },
      duration: 0,
      bearing: 0,
      pitch: 0
    });
    frame.classList.add("map-ready");
  });
}


const WALK_STEPS = [
  {
    code: "SB",
    label: "Silk Board",
    confidence: 18,
    title: "Vehicle enters at Silk Board",
    body: "PTIS starts from a prior belief. Six possible destinations remain, so the system observes without acting."
  },
  {
    code: "HSR",
    label: "HSR Layout",
    confidence: 22,
    title: "Passed Silk Board without turning",
    body: "The vehicle did not exit immediately. One local possibility becomes less likely, and Whitefield belief rises to 22%."
  },
  {
    code: "SW",
    label: "Sony World",
    confidence: 34,
    title: "Passed HSR Layout without turning",
    body: "Another junction is eliminated from the destination set. PTIS now has stronger evidence that the flow is continuing downstream."
  },
  {
    code: "MH",
    label: "Marathahalli",
    confidence: 67,
    title: "Belief crosses the action threshold",
    body: "At Marathahalli, Whitefield belief reaches 67%. PTIS marks the connector decision as eligible, then checks receiving-road capacity before any command is allowed.",
    eligible: true
  },
  {
    code: "DK",
    label: "Doddanekkundi",
    confidence: 82,
    title: "Downstream evidence keeps increasing",
    body: "Continued movement after Marathahalli strengthens the destination belief. The capacity gate still prevents over-commanding the receiving road."
  },
  {
    code: "WF",
    label: "Whitefield",
    confidence: 100,
    title: "Replay destination observed",
    body: "In this software replay, the trace reaches Whitefield. That confirms the replay path for this example, not a live field-deployment result.",
    final: true
  }
];

let walkIndex = 0;

function renderWalkthrough(route) {
  const track = q("#walk-track");
  if (!track) return;
  const routeKm = route?.distance_m ? km(route.distance_m) : "route grounded";
  setText("#walk-route-summary", `6 junctions / ${routeKm}`);
  track.innerHTML = WALK_STEPS.map((step, index) => `
    <button class="walk-node" type="button" role="tab" data-walk-index="${index}" aria-selected="false">
      <span class="walk-node-dot"><span class="walk-node-code">${step.code}</span></span>
      <span class="walk-node-label">${step.label}</span>
      <span class="walk-node-prob"></span>
    </button>
  `).join("");
  track.addEventListener("click", event => {
    const button = event.target.closest("[data-walk-index]");
    if (!button) return;
    walkIndex = Number(button.dataset.walkIndex || 0);
    updateWalkthrough();
  });
  q("#walk-prev")?.addEventListener("click", () => {
    walkIndex = Math.max(0, walkIndex - 1);
    updateWalkthrough();
  });
  q("#walk-next")?.addEventListener("click", () => {
    walkIndex = Math.min(WALK_STEPS.length - 1, walkIndex + 1);
    updateWalkthrough();
  });
  q("#walk-reset")?.addEventListener("click", () => {
    walkIndex = 0;
    updateWalkthrough();
  });
  updateWalkthrough();
}

function updateWalkthrough() {
  const step = WALK_STEPS[walkIndex] || WALK_STEPS[0];
  const track = q("#walk-track");
  if (track) {
    const progress = WALK_STEPS.length <= 1 ? 0 : (walkIndex / (WALK_STEPS.length - 1)) * 100;
    track.style.setProperty("--progress-ratio", String(progress / 100));
    track.querySelectorAll(".walk-node").forEach((node, index) => {
      const item = WALK_STEPS[index];
      node.classList.toggle("is-passed", index < walkIndex);
      node.classList.toggle("is-active", index === walkIndex && !item.eligible && !item.final);
      node.classList.toggle("is-eligible", index === walkIndex && Boolean(item.eligible));
      node.classList.toggle("is-final", index === walkIndex && Boolean(item.final));
      node.setAttribute("aria-selected", String(index === walkIndex));
      const prob = node.querySelector(".walk-node-prob");
      if (prob) prob.textContent = index < walkIndex ? `${item.confidence}%` : "";
    });
  }
  setText("#walk-confidence", `${step.confidence}%`);
  const bar = q("#walk-progress-bar");
  if (bar) bar.style.width = `${step.confidence}%`;
  const progress = q(".walk-progress");
  if (progress) progress.classList.toggle("is-eligible", step.confidence >= 65);
  const card = q("#walk-card");
  if (card) {
    card.classList.toggle("is-eligible", Boolean(step.eligible));
    card.classList.toggle("is-final", Boolean(step.final));
    card.innerHTML = `<h3>${step.title}</h3><p>${step.body}</p>`;
  }
  setText("#walk-position", `Junction ${walkIndex + 1} / ${WALK_STEPS.length}`);
  const prev = q("#walk-prev");
  const next = q("#walk-next");
  if (prev) prev.disabled = walkIndex === 0;
  if (next) {
    next.disabled = walkIndex === WALK_STEPS.length - 1;
    next.textContent = walkIndex === WALK_STEPS.length - 2 ? "Finish replay" : "Next junction";
  }
}


async function init() {
  try {
    const [latest, suite, extreme, cctv, route, official] = await Promise.all([
      loadJson(DATA.latest),
      loadJson(DATA.suite),
      loadJson(DATA.extreme),
      loadJson(DATA.cctv),
      loadJson(DATA.route),
      loadJson(DATA.official)
    ]);
    renderNumbers({ latest, suite, extreme, cctv, route, official });
    renderWalkthrough(route);
    renderFallback(route, latest, extreme);
    initMapLibre(route, latest, extreme);
  } catch (error) {
    console.error(error);
    setText("#hero-action", "Could not load local evidence files. Check the frontend server path.");
    setText("#route-distance", "Evidence load failed");
  }
}

init();
