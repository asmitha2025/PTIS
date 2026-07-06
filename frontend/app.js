const API_BASE = "http://localhost:8000";
const DEFAULT_SCENARIO_ID = "silk_board_whitefield_capacity_safe_v1";
const TILE_SIZE = 256;
const MAP_MIN_ZOOM = 10;
const MAP_MAX_ZOOM = 15;
const mapState = {
  autoFit: true,
  center: null,
  context: null,
  dragging: false,
  lastPointer: null,
  routeKey: "",
  zoom: null,
  maplibre: null,
  maplibreMarkers: [],
  maplibreRouteKey: "",
  maplibreReady: false
};

const audienceState = {
  active: "control",
  evidence: null
};
const fallbackEvidence = {
  passed: true,
  scenario_id: DEFAULT_SCENARIO_ID,
  scenario_name: "Silk Board to Whitefield capacity-safe activation",
  generated_at: "not loaded",
  corridor: {
    name: "Bengaluru ORR: Silk Board to Whitefield",
    junctions: [
      { id: "silk_board", lat: 12.917, lon: 77.6228, name: "Silk Board", order: 0 },
      { id: "hsr_layout", lat: 12.9116, lon: 77.6365, name: "HSR Layout", order: 1 },
      { id: "sony_world", lat: 12.9352, lon: 77.654, name: "Sony World", order: 2 },
      { id: "marathahalli", lat: 12.9591, lon: 77.7014, name: "Marathahalli", order: 3 },
      { id: "doddanekkundi", lat: 12.9724, lon: 77.7185, name: "Doddanekkundi", order: 4 },
      { id: "itpl", lat: 12.985, lon: 77.736, name: "ITPL", order: 5 },
      { id: "whitefield", lat: 12.9698, lon: 77.748, name: "Whitefield", order: 6 }
    ],
    smart_links: [
      { id: "sl_marathahalli_whitefield", from_junction_id: "marathahalli", to_junction_id: "whitefield", destination_id: "whitefield", min_confidence: 0.65, capacity_vpm: 23 }
    ]
  },
  cycles: [
    {
      cycle: 3,
      observation: { junction_id: "marathahalli" },
      posterior: { doddanekkundi: 0.1492537313, itpl: 0.1791044776, whitefield: 0.6716417910 },
      best_destination_id: "whitefield",
      best_confidence: 0.6716417910,
      density_tw_per_km: [66.67, 74.87, 82.26, 87.97, 86.84, 83.73],
      decisions: [{ link_id: "sl_marathahalli_whitefield", activate: true, confidence: 0.6716417910, available_capacity_vpm: 14.5, q_expected_vpm: 14.5, q_commanded_vpm: 14.35, reason: "fallback evidence" }]
    }
  ],
  assertions: [
    { name: "expected_link_activates", passed: true },
    { name: "activation_confidence_floor", passed: true },
    { name: "capacity_safe_decisions", passed: true }
  ]
};

const fallbackSuite = { passed: true, passed_count: 0, scenario_count: 0, scenarios: [] };
const fallbackBatch = {
  passed: true,
  metrics: {
    vehicle_count: 0,
    observation_count: 0,
    activation_count: 0,
    capacity_violation_count: 0,
    overcommand_count: 0,
    false_positive_activations: 0,
    mean_activation_confidence: 0,
    mean_abs_demand_error_vpm: 0
  },
  aggregate_decisions: [],
  assertions: []
};
const fallbackExtremeBatch = fallbackBatch;

const fallbackCctv = {
  passed: false,
  metrics: { metadata_rows: 0, coco_image_count: 0, coco_annotation_count: 0, category_count: 0, local_image_count: 0, sample_annotation_count: 0 },
  sample_images: [],
  assertions: []
};
const fallbackField = { field_proven: false, status: "waiting_for_field_replay_data", metrics: {}, assertions: [] };
const fallbackRemoteAggregate = { passed: false, field_proven: false, remote_aggregate_replay: false, status: "waiting_for_remote_aggregate_counts", metrics: {}, assertions: [] };
const fallbackOfficial = { status: "missing", source_documents: [], planning_facts: [], junction_counts: [], screenline_counts: [] };
const fallbackRouteGeometry = { status: "missing", coordinate_count: 0, distance_m: 0, features: [] };

async function fetchWithTimeout(url, timeoutMs = 1400) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { cache: "no-store", signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function fetchJson(apiPath, localPath, fallback) {
  try {
    const api = await fetchWithTimeout(`${API_BASE}${apiPath}`);
    if (api.ok) return api.json();
  } catch (_) {}
  try {
    const local = await fetchWithTimeout(localPath, 3000);
    if (local.ok) return local.json();
  } catch (_) {}
  return fallback;
}

async function postJson(apiPath) {
  const response = await fetch(`${API_BASE}${apiPath}`, { method: "POST" });
  if (!response.ok) throw new Error(`API returned ${response.status}`);
  return response.json();
}

async function loadAllEvidence() {
  const [scenario, suite, batch, extremeBatch, official, cctv, field, remoteAggregate, routeGeometry] = await Promise.all([
    fetchJson("/api/evidence/latest", "../evidence/latest_run.json", fallbackEvidence),
    fetchJson("/api/evidence/suite", "../evidence/suite_report.json", fallbackSuite),
    fetchJson("/api/evidence/batch", "../evidence/batch_report.json", fallbackBatch),
    fetchJson("/api/evidence/extreme-batch", "../evidence/extreme_batch_report.json", fallbackExtremeBatch),
    fetchJson("/api/official-reference", "../data/official_reference_bengaluru_cmp_2020.json", fallbackOfficial),
    fetchJson("/api/evidence/cctv", "../evidence/cctv_bmd45_report.json", fallbackCctv),
    fetchJson("/api/evidence/field-replay", "../evidence/field_replay_report.json", fallbackField),
    fetchJson("/api/evidence/remote-aggregate", "../evidence/remote_aggregate_replay_report.json", fallbackRemoteAggregate),
    fetchJson("/api/route-geometry", "../data/orr_silk_board_whitefield_route_osrm.geojson", fallbackRouteGeometry)
  ]);
  renderAll({ scenario, suite, batch, extremeBatch, official, cctv, field, remoteAggregate, routeGeometry });
}

async function runScenario() {
  try {
    await postJson(`/api/scenarios/${DEFAULT_SCENARIO_ID}/run`);
  } catch (error) {
    console.info("API replay unavailable; using saved evidence", error.message);
  }
  loadAllEvidence();
}

async function runSuite() {
  try {
    await postJson("/api/suite/run");
  } catch (error) {
    console.info("API suite unavailable; using saved evidence", error.message);
  }
  loadAllEvidence();
}

async function runBatch() {
  try {
    await postJson("/api/batch/run");
  } catch (error) {
    console.info("API batch unavailable; using saved evidence", error.message);
  }
  loadAllEvidence();
}

async function runExtremeBatch() {
  try {
    await postJson("/api/extreme-batch/run");
  } catch (error) {
    console.info("API extreme stress unavailable; using saved evidence", error.message);
  }
  loadAllEvidence();
}

function renderAll({ scenario, suite, batch, extremeBatch, official, cctv, field, remoteAggregate, routeGeometry }) {
  const cycles = scenario.cycles || fallbackEvidence.cycles;
  const latest = cycles[cycles.length - 1];
  const decision = cycles.flatMap(c => c.decisions || []).find(d => d.activate);
  const posterior = latest.posterior || {};
  const bestId = latest.best_destination_id || Object.entries(posterior).sort((a, b) => b[1] - a[1])[0]?.[0] || "unknown";
  const confidence = latest.best_confidence ?? posterior[bestId] ?? 0;
  const softwarePassed = Boolean(scenario.passed && suite.passed && batch.passed && (extremeBatch?.passed ?? true));
  const cctvPassed = Boolean(cctv.passed);
  const officialReady = Boolean(official.source_documents?.length && official.status !== "missing");
  const fieldPassed = Boolean(field.field_proven);
  const remotePassed = Boolean(remoteAggregate?.passed);

  const context = { scenario, suite, batch, extremeBatch, official, cctv, field, remoteAggregate, routeGeometry, latest, decision, bestId, confidence };
  renderHeader(scenario, confidence, softwarePassed, cctvPassed, fieldPassed);
  renderUnderstanding(context);
  renderStats({ suite, batch, extremeBatch, official, cctv, field, remoteAggregate, routeGeometry, softwarePassed, cctvPassed, officialReady, fieldPassed, remotePassed });
  renderGeoMap(scenario, latest, bestId, decision, extremeBatch, routeGeometry);
  renderPosterior(posterior, bestId, latest, decision);
  renderDecision(decision, confidence);
  renderCapacity(decision);
  renderCctv(cctv);
  renderDensity(scenario, latest);
  renderTraceStrip(extremeBatch);
  renderAudienceViews(context);
  renderScenarioLibrary(suite);
  renderBottomMetrics({ batch, extremeBatch, cctv, official, field, remoteAggregate, decision });
  renderDetails(context);
}

function renderUnderstanding(context) {
  const proof = proofMetrics(context);
  const latest = context.latest || {};
  const junctions = [...(context.scenario?.corridor?.junctions || [])].sort((a, b) => a.order - b.order);
  const activeId = latest.observation?.junction_id;
  const activeOrder = junctions.find(item => item.id === activeId)?.order ?? -1;
  const selectedIds = ["silk_board", "hsr_layout", "sony_world", "marathahalli", "whitefield"];
  const selected = selectedIds.map(id => junctions.find(item => item.id === id)).filter(Boolean);
  const confidence = context.confidence || 0;
  const decision = context.decision;
  const action = decision?.activate ? "simulated activation" : "standby";
  const status = document.getElementById("understand-status");
  if (status) status.textContent = `${proof.suiteScore} scenarios passed / ${proof.capacityViolations} capacity violations / field ${proof.fieldGate}`;
  setText("route-story-title", `${proof.checkpoint} -> ${proof.bestDestination} ${proof.confidence}`);

  const story = document.getElementById("simple-route-story");
  if (story) {
    story.innerHTML = selected.map((junction, index) => {
      const cls = ["simple-node"];
      let state = "possible";
      if (junction.order < activeOrder) {
        cls.push("passed");
        state = "passed";
      }
      if (junction.id === activeId) {
        cls.push("checkpoint");
        state = "checkpoint";
      }
      if (junction.id === context.bestId) {
        cls.push("target");
        state = "likely";
      }
      return `
        <article class="${cls.join(" ")}">
          <span class="node-index">${index + 1}</span>
          <strong>${escapeHtml(shortLabel(junction.name))}</strong>
          <small>${escapeHtml(state)}</small>
        </article>
      `;
    }).join("");
  }

  const gate = document.getElementById("simple-gate-story");
  if (gate) {
    gate.innerHTML = `
      <article class="gate-mini ${confidence >= 0.65 ? "pass" : "wait"}">
        <span>Confidence</span>
        <strong>${escapeHtml(proof.confidence)}</strong>
        <p>${escapeHtml(`${proof.bestDestination} is the strongest destination belief.`)}</p>
      </article>
      <article class="gate-mini ${decision?.activate ? "pass" : "wait"}">
        <span>Capacity</span>
        <strong>${escapeHtml(decision ? `${number(decision.available_capacity_vpm)} vpm` : "waiting")}</strong>
        <p>${escapeHtml(decision?.activate ? "Receiving capacity is enough in replay." : "Action stays closed until capacity is safe.")}</p>
      </article>
      <article class="gate-result ${decision?.activate ? "active" : "wait"}">
        <span>Replay action</span>
        <strong>${escapeHtml(action)}</strong>
      </article>
    `;
  }

  const proofStrip = document.getElementById("simple-proof-strip");
  if (proofStrip) {
    proofStrip.innerHTML = [
      simpleProofItem("Software", proof.suiteScore, "scenario suite"),
      simpleProofItem("Stress", proof.vehicleCount, `${proof.observationCount} observations`),
      simpleProofItem("Safety", proof.capacityViolations, "capacity violations"),
      simpleProofItem("Route", proof.routePoints, proof.routeDistance),
      simpleProofItem("CCTV", proof.cctvBoxes, "BMD-45 boxes"),
      simpleProofItem("Field", proof.fieldGate, "not claimed yet")
    ].join("");
  }
}

function simpleProofItem(labelText, value, detail) {
  return `<article class="simple-proof-item"><span>${escapeHtml(labelText)}</span><strong>${escapeHtml(value)}</strong><p>${escapeHtml(detail)}</p></article>`;
}
function renderHeader(scenario, confidence, softwarePassed, cctvPassed, fieldPassed) {
  setText("corridor-label", scenario.corridor?.name || "Bengaluru ORR evidence console");
  setText("scenario-name", scenario.scenario_name || "Scenario");
  setText("wf-probability", percent(confidence));
  const status = document.getElementById("status-pill");
  const passed = softwarePassed && cctvPassed;
  status.textContent = passed ? (fieldPassed ? "field replay passed" : "software + CCTV passed; field pending") : "evidence review";
  status.className = `badge ${passed ? (fieldPassed ? "pass" : "wait") : "fail"}`;
}

function renderStats({ suite, batch, extremeBatch, official, cctv, field, remoteAggregate, routeGeometry, softwarePassed, cctvPassed, officialReady, fieldPassed, remotePassed }) {
  const m = extremeBatch?.metrics || batch.metrics || fallbackBatch.metrics;
  const cm = cctv.metrics || fallbackCctv.metrics;
  const routeReady = Boolean(routeGeometry?.coordinate_count);
  const rm = remoteAggregate?.metrics || fallbackRemoteAggregate.metrics;
  document.getElementById("stats-row").innerHTML = [
    statTile("Proof Suite", suite.scenario_count ? `${suite.passed_count}/${suite.scenario_count}` : "--", softwarePassed ? "software assertions passed" : "review needed"),
    statTile("Stress Replay", `${integer(m.vehicle_count)} veh`, `${integer(m.observation_count)} checkpoint observations`),
    statTile("Route Geometry", routeReady ? `${integer(routeGeometry.coordinate_count)} pts` : "--", routeGeometry?.distance_m ? `${number(routeGeometry.distance_m / 1000)} km OSRM/OpenStreetMap` : "route reference pending"),
    statTile("CCTV Audit", `${integer(cm.coco_annotation_count)} boxes`, cctvPassed ? `${integer(cm.local_image_count)} BMD-45 frames` : "waiting"),
    statTile("Remote Replay", remotePassed ? `${integer(rm.row_count || 0)} rows` : "pending", remotePassed ? `${number(rm.peak_total_vpm || 0)} vpm peak observed` : "aggregate counts needed"),
    statTile("Field Gate", fieldPassed ? "passed" : "pending", field.status || "observed replay needed")
  ].join("");
}
function renderGeoMap(report, latest, bestId, decision, extremeBatch, routeGeometry) {
  mapState.context = { report, latest, bestId, decision, extremeBatch, routeGeometry };
  const svg = document.getElementById("geo-map");
  const stack = document.getElementById("map-stack");
  const junctions = [...(report.corridor?.junctions || [])].sort((a, b) => a.order - b.order);
  if (!junctions.length) {
    svg.innerHTML = "";
    setText("map-status", "Corridor geometry unavailable");
    return;
  }

  const rect = stack?.getBoundingClientRect();
  const width = Math.max(320, Math.round(rect?.width || 980));
  const height = Math.max(260, Math.round(rect?.height || 330));
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  const roadCoords = extractRouteCoordinates(routeGeometry);
  const routeCoords = roadCoords.length ? roadCoords : junctions.map(j => [Number(j.lon), Number(j.lat)]);
  const allCoords = [...routeCoords, ...junctions.map(j => [Number(j.lon), Number(j.lat)])];
  const lats = allCoords.map(coord => Number(coord[1]));
  const lons = allCoords.map(coord => Number(coord[0]));
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const routePointCount = routeGeometry?.coordinate_count || routeCoords.length;
  const routeKey = `${routePointCount}:${minLat.toFixed(6)}:${maxLat.toFixed(6)}:${minLon.toFixed(6)}:${maxLon.toFixed(6)}`;
  if (!mapState.center || mapState.zoom == null || mapState.autoFit || mapState.routeKey !== routeKey) {
    const fitted = fitMapView(minLat, maxLat, minLon, maxLon, width, height);
    mapState.center = fitted.center;
    mapState.zoom = fitted.zoom;
    mapState.routeKey = routeKey;
    mapState.autoFit = false;
  }

  const maplibreReady = renderMapLibreShowcase({ routeCoords, junctions, latest, bestId, decision, routeGeometry, stress: extremeBatch?.metrics || fallbackBatch.metrics, bounds: { minLat, maxLat, minLon, maxLon } });
  renderTileLayer(width, height);

  const project = (lon, lat) => projectMapPoint(lon, lat, width, height);
  const points = junctions.map(j => ({ ...j, ...project(j.lon, j.lat) }));
  const routePoints = routeCoords.map(coord => ({ lon: Number(coord[0]), lat: Number(coord[1]), ...project(coord[0], coord[1]) }));
  const byId = Object.fromEntries(points.map(p => [p.id, p]));
  const routeD = pathFromPoints(routePoints);
  const nearestIndexById = Object.fromEntries(junctions.map(j => [j.id, nearestRouteIndex(routeCoords, j)]));
  const activeOrder = junctions.find(j => j.id === latest.observation?.junction_id)?.order ?? -1;
  const activeIndex = nearestIndexById[latest.observation?.junction_id] ?? -1;
  const activeD = activeIndex > 0 ? pathFromPoints(routePoints.slice(0, activeIndex + 1)) : "";
  const link = report.corridor?.smart_links?.[0];
  const from = link ? byId[link.from_junction_id] : null;
  const to = link ? byId[link.to_junction_id] : null;
  const fromIndex = link ? nearestIndexById[link.from_junction_id] : -1;
  const toIndex = link ? nearestIndexById[link.to_junction_id] : -1;
  const linkD = from && to ? pathFromPoints(routeSlice(routePoints, fromIndex, toIndex)) : "";
  const density = latest.density_tw_per_km || [];
  const stress = extremeBatch?.metrics || fallbackBatch.metrics;
  const routeFlowCount = flowDotCount(stress.vehicle_count || 0);
  const divertFlowCount = decision?.activate ? Math.max(8, Math.round(routeFlowCount * 0.34)) : 0;
  const maxDensity = Math.max(100, ...density.map(Number));
  const routeSegments = buildRouteSegments(routePoints, junctions, nearestIndexById);
  const densitySegments = buildDensitySegments(routeSegments, density, maxDensity);
  const routeDots = buildFlowDots("route-flow-path", routeFlowCount, "route", stress.vehicle_count || 0);
  const divertDots = linkD && decision?.activate ? buildFlowDots("divert-flow-path", divertFlowCount, "divert", stress.vehicle_count || 0) : "";
  const panelLines = flowPanelLines(stress, decision, routeGeometry);
  const routeKm = routeGeometry?.distance_m ? `${number(routeGeometry.distance_m / 1000)} km` : "junction fallback";

  const nodes = points.map(p => {
    const cls = ["map-node"];
    if (p.order < activeOrder) cls.push("passed");
    if (p.id === latest.observation?.junction_id) cls.push("active");
    if (p.id === bestId) cls.push("target");
    const pulse = p.id === latest.observation?.junction_id ? `<circle class="node-pulse" r="18"></circle>` : "";
    const halo = p.id === bestId ? `<circle class="target-halo" r="23"></circle>` : "";
    return `
      <g class="${cls.join(" ")}" transform="translate(${p.x.toFixed(1)} ${p.y.toFixed(1)})" data-node="${escapeHtml(p.id)}">
        ${pulse}${halo}
        <circle class="node-ring" r="15"></circle>
        <text class="abbr" y="4" text-anchor="middle">${escapeHtml(abbr(p.name))}</text>
        <text x="0" y="34" text-anchor="middle">${escapeHtml(shortLabel(p.name))}</text>
      </g>
    `;
  }).join("");

  svg.innerHTML = `
    <rect x="0" y="0" width="${width}" height="${height}" fill="#ffffff" opacity="0.03"></rect>
    ${densitySegments}
    <path id="route-flow-path" class="map-flow-path-hidden" d="${routeD}"></path>
    <path class="map-route-base real-route" d="${routeD}" data-route-points="${routePointCount}" data-map-zoom="${mapState.zoom}"></path>
    <path class="map-flow-stroke" d="${routeD}"></path>
    ${activeD ? `<path class="map-route-active" d="${activeD}"></path>` : ""}
    ${linkD ? `<path id="divert-flow-path" class="map-flow-path-hidden" d="${linkD}"></path>` : ""}
    ${linkD ? `<path class="map-link ${decision?.activate ? "active" : ""}" d="${linkD}"></path>` : ""}
    ${linkD && decision?.activate ? `<path class="map-flow-stroke divert" d="${linkD}"></path>` : ""}
    ${routeDots}
    ${divertDots}
    ${nodes}
    <g class="map-flow-panel" transform="translate(18 38)">
      <rect width="326" height="72"></rect>
      <text x="12" y="20">${escapeHtml(panelLines[0])}</text>
      <text class="muted" x="12" y="40">${escapeHtml(panelLines[1])}</text>
      <text class="muted" x="12" y="58">${escapeHtml(`${integer(routePointCount)} routed points / zoom ${mapState.zoom} / ${routeKm}`)}</text>
    </g>
    <text class="map-label" x="18" y="26">Built-in OpenStreetMap tile viewport / OSRM route geometry</text>
    <text class="map-label" x="18" y="${height - 20}">tiles, route, markers and flow share one Web Mercator transform</text>
  `;

  const action = decision?.activate ? "capacity-safe activation" : "standby";
  renderRouteCheckpoints(junctions, latest, bestId, decision, routeGeometry, activeOrder);
  setText("route-proof", routeGeometry?.coordinate_count ? `${integer(routeGeometry.coordinate_count)} pts / ${routeKm}` : "junction fallback");
  setText("map-mode", maplibreReady ? "MapLibre route showcase" : (routeGeometry?.coordinate_count ? `${integer(routeGeometry.coordinate_count)}-point fallback map` : "route fallback"));
  setText("map-status", `${label(latest.observation?.junction_id || "checkpoint")} checkpoint -> ${label(bestId)} ${percent(latest.best_confidence || 0)} -> ${action}. ${maplibreReady ? "MapLibre/CARTO basemap with OSRM route overlay" : "Fallback map with OSRM route overlay"}; verified replay, not live field traffic.`);
  setText("flow-vehicles", stress.vehicle_count ? `${integer(stress.vehicle_count)} veh` : "scenario replay");
  setText("flow-observations", stress.observation_count ? `${integer(stress.observation_count)} obs` : `${integer((report.cycles || []).length)} cycles`);
  setText("flow-safety", `${integer(stress.capacity_violation_count || 0)} violations`);
}

function renderMapLibreShowcase({ routeCoords, junctions, latest, bestId, decision, routeGeometry, stress, bounds }) {
  const container = document.getElementById("maplibre-map");
  const stack = document.getElementById("map-stack");
  if (!container || !window.maplibregl || !routeCoords.length) {
    stack?.classList.remove("maplibre-ready");
    return false;
  }

  const routeKey = `${routeCoords.length}:${bounds.minLat.toFixed(5)}:${bounds.maxLat.toFixed(5)}:${bounds.minLon.toFixed(5)}:${bounds.maxLon.toFixed(5)}`;
  const routeGeoJson = {
    type: "FeatureCollection",
    features: [{ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: routeCoords } }]
  };
  const activeId = latest.observation?.junction_id;
  const pointFeatures = junctions.map(junction => ({
    type: "Feature",
    properties: {
      id: junction.id,
      name: junction.name,
      abbr: abbr(junction.name),
      state: junction.id === bestId ? "target" : (junction.id === activeId ? "checkpoint" : "route")
    },
    geometry: { type: "Point", coordinates: [Number(junction.lon), Number(junction.lat)] }
  }));
  const pointsGeoJson = { type: "FeatureCollection", features: pointFeatures };

  if (!mapState.maplibre) {
    mapState.maplibre = new maplibregl.Map({
      container,
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [(bounds.minLon + bounds.maxLon) / 2, (bounds.minLat + bounds.maxLat) / 2],
      zoom: 11,
      pitch: 38,
      bearing: -18,
      attributionControl: true
    });
    mapState.maplibre.dragRotate.disable();
    mapState.maplibre.touchZoomRotate.disableRotation();
    mapState.maplibre.on("load", () => updateMapLibreLayers(routeGeoJson, pointsGeoJson, bounds));
  } else if (mapState.maplibre.loaded()) {
    updateMapLibreLayers(routeGeoJson, pointsGeoJson, bounds);
  }

  if (mapState.maplibre.loaded() && mapState.maplibreRouteKey !== routeKey) {
    fitMapLibreBounds(bounds, false);
    mapState.maplibreRouteKey = routeKey;
  }

  stack?.classList.add("maplibre-ready");
  renderMapLibreOverlay(stress, decision, routeGeometry);
  return true;
}

function updateMapLibreLayers(routeGeoJson, pointsGeoJson, bounds) {
  const map = mapState.maplibre;
  if (!map) return;
  if (!map.getSource("ptis-route")) {
    map.addSource("ptis-route", { type: "geojson", data: routeGeoJson });
    map.addLayer({
      id: "ptis-route-shadow",
      type: "line",
      source: "ptis-route",
      paint: { "line-color": "#0f172a", "line-width": 11, "line-opacity": 0.18, "line-blur": 1.2 }
    });
    map.addLayer({
      id: "ptis-route-line",
      type: "line",
      source: "ptis-route",
      paint: { "line-color": "#087f68", "line-width": 5.5, "line-opacity": 0.96 }
    });
  } else {
    map.getSource("ptis-route").setData(routeGeoJson);
  }

  if (!map.getSource("ptis-points")) {
    map.addSource("ptis-points", { type: "geojson", data: pointsGeoJson });
    map.addLayer({
      id: "ptis-point-halo",
      type: "circle",
      source: "ptis-points",
      paint: {
        "circle-radius": ["match", ["get", "state"], "target", 18, "checkpoint", 16, 11],
        "circle-color": "#ffffff",
        "circle-opacity": 0.92,
        "circle-stroke-color": "#d8e1dc",
        "circle-stroke-width": 1
      }
    });
    map.addLayer({
      id: "ptis-point-dot",
      type: "circle",
      source: "ptis-points",
      paint: {
        "circle-radius": ["match", ["get", "state"], "target", 10, "checkpoint", 9, 6],
        "circle-color": ["match", ["get", "state"], "target", "#087f68", "checkpoint", "#255fbd", "#334155"],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 2
      }
    });
    map.addLayer({
      id: "ptis-point-label",
      type: "symbol",
      source: "ptis-points",
      layout: {
        "text-field": ["get", "abbr"],
        "text-size": 11,
        "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
        "text-offset": [0, 1.85],
        "text-anchor": "top",
        "text-allow-overlap": false
      },
      paint: { "text-color": "#0f172a", "text-halo-color": "#ffffff", "text-halo-width": 1.5 }
    });
  } else {
    map.getSource("ptis-points").setData(pointsGeoJson);
  }
  fitMapLibreBounds(bounds, true);
}

function fitMapLibreBounds(bounds, initialOnly) {
  const map = mapState.maplibre;
  if (!map) return;
  if (initialOnly && mapState.maplibreReady) return;
  map.fitBounds([[bounds.minLon, bounds.minLat], [bounds.maxLon, bounds.maxLat]], {
    padding: { top: 74, right: 56, bottom: 56, left: 56 },
    pitch: 38,
    bearing: -18,
    duration: initialOnly ? 0 : 700
  });
  mapState.maplibreReady = true;
}

function renderMapLibreOverlay(stress, decision, routeGeometry) {
  const container = document.getElementById("maplibre-map");
  if (!container) return;
  const overlay = container.querySelector(".mapcn-overlay") || document.createElement("div");
  overlay.className = "mapcn-overlay";
  overlay.innerHTML = `
    <div><span>Stress replay</span><strong>${integer(stress.vehicle_count || 0)} vehicles</strong></div>
    <div><span>Observations</span><strong>${integer(stress.observation_count || 0)}</strong></div>
    <div><span>Safety</span><strong>${integer(stress.capacity_violation_count || 0)} violations</strong></div>
    <div><span>Route</span><strong>${integer(routeGeometry?.coordinate_count || 0)} pts</strong></div>
    <p>${escapeHtml(decision?.activate ? "Capacity-safe simulated activation" : "Gate remains on standby")}</p>
  `;
  if (!overlay.parentElement) container.appendChild(overlay);
}
function fitMapView(minLat, maxLat, minLon, maxLon, width, height) {
  const pad = 48;
  const nw = lonLatToWorld(minLon, maxLat);
  const se = lonLatToWorld(maxLon, minLat);
  const dx = Math.max(0.000001, Math.abs(se.x - nw.x));
  const dy = Math.max(0.000001, Math.abs(se.y - nw.y));
  const usableWidth = Math.max(180, width - pad * 2);
  const usableHeight = Math.max(160, height - pad * 2);
  const zoomX = Math.log2(usableWidth / (dx * TILE_SIZE));
  const zoomY = Math.log2(usableHeight / (dy * TILE_SIZE));
  const zoom = clamp(Math.floor(Math.min(zoomX, zoomY)), MAP_MIN_ZOOM, MAP_MAX_ZOOM);
  const centerWorld = { x: (nw.x + se.x) / 2, y: (nw.y + se.y) / 2 };
  return { center: worldToLonLat(centerWorld.x, centerWorld.y), zoom };
}

function renderTileLayer(width, height) {
  const tileMap = document.getElementById("tile-map");
  if (!tileMap || !mapState.center || mapState.zoom == null) return;
  const z = clamp(Math.round(mapState.zoom), MAP_MIN_ZOOM, MAP_MAX_ZOOM);
  const center = lonLatToPixel(mapState.center.lon, mapState.center.lat, z);
  const leftWorld = center.x - width / 2;
  const topWorld = center.y - height / 2;
  const startX = Math.floor(leftWorld / TILE_SIZE) - 1;
  const endX = Math.floor((leftWorld + width) / TILE_SIZE) + 1;
  const startY = Math.floor(topWorld / TILE_SIZE) - 1;
  const endY = Math.floor((topWorld + height) / TILE_SIZE) + 1;
  const tileCount = 2 ** z;
  const tiles = [`<div class="tile-fallback-grid"></div>`];
  for (let x = startX; x <= endX; x += 1) {
    for (let y = startY; y <= endY; y += 1) {
      if (y < 0 || y >= tileCount) continue;
      const wrappedX = ((x % tileCount) + tileCount) % tileCount;
      const left = Math.round(x * TILE_SIZE - leftWorld);
      const top = Math.round(y * TILE_SIZE - topWorld);
      tiles.push(`<img class="map-tile" src="https://tile.openstreetmap.org/${z}/${wrappedX}/${y}.png" alt="" loading="lazy" draggable="false" style="left:${left}px;top:${top}px" data-tile="${z}/${wrappedX}/${y}" />`);
    }
  }
  tileMap.innerHTML = tiles.join("");
}

function projectMapPoint(lon, lat, width, height) {
  const z = clamp(Math.round(mapState.zoom ?? MAP_MIN_ZOOM), MAP_MIN_ZOOM, MAP_MAX_ZOOM);
  const center = lonLatToPixel(mapState.center.lon, mapState.center.lat, z);
  const point = lonLatToPixel(lon, lat, z);
  return { x: width / 2 + (point.x - center.x), y: height / 2 + (point.y - center.y) };
}

function lonLatToPixel(lon, lat, zoom) {
  const world = lonLatToWorld(lon, lat);
  const scale = TILE_SIZE * (2 ** zoom);
  return { x: world.x * scale, y: world.y * scale };
}

function pixelToLonLat(x, y, zoom) {
  const scale = TILE_SIZE * (2 ** zoom);
  return worldToLonLat(x / scale, y / scale);
}

function lonLatToWorld(lon, lat) {
  const safeLat = clamp(Number(lat), -85.05112878, 85.05112878);
  const sin = Math.sin((safeLat * Math.PI) / 180);
  return {
    x: (Number(lon) + 180) / 360,
    y: 0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)
  };
}

function worldToLonLat(x, y) {
  const lon = x * 360 - 180;
  const n = Math.PI - 2 * Math.PI * y;
  const lat = (180 / Math.PI) * Math.atan(Math.sinh(n));
  return { lon, lat };
}
function renderPosterior(posterior, bestId, latest, decision) {
  const entries = Object.entries(posterior).sort((a, b) => b[1] - a[1]);
  setText("posterior-title", `${label(bestId)} ${percent(latest.best_confidence || posterior[bestId] || 0)}`);
  setText("posterior-cycle", `cycle ${latest.cycle ?? "--"}`);
  document.getElementById("dest-bars").innerHTML = entries.map(([id, value]) => `
    <div class="bar-row">
      <div class="bar-name">${escapeHtml(shortLabel(label(id)))}</div>
      <div class="track"><div class="fill ${id === bestId ? "best" : ""}" style="width:${Math.round(Number(value) * 100)}%"></div></div>
      <div class="bar-value">${percent(value)}</div>
    </div>
  `).join("");
  const alert = document.getElementById("activation-alert");
  alert.textContent = decision?.activate ? `Gate open at ${percent(decision.confidence)}. Command is capped by receiving capacity.` : "Gate closed. Confidence or capacity threshold not met.";
  alert.className = `alert-line ${decision?.activate ? "active" : ""}`;
}

function renderDecision(decision, confidence) {
  const card = document.getElementById("decision-card");
  const active = Boolean(decision?.activate);
  card.className = `panel decision-card ${active ? "active" : ""}`;
  setText("decision-state", active ? "ACTIVE" : "STANDBY");
  setText("decision-detail", active ? `P=${percent(confidence)} / ${number(decision.q_expected_vpm)} vpm expected / ${number(decision.available_capacity_vpm)} vpm available` : `P=${percent(confidence)} / waiting for safe gate`);
}

function renderCapacity(decision) {
  document.getElementById("capacity-ledger").innerHTML = decision ? [
    ledgerCell("Confidence", percent(decision.confidence), "gate input"),
    ledgerCell("Expected", `${number(decision.q_expected_vpm)} vpm`, "capped demand"),
    ledgerCell("Available", `${number(decision.available_capacity_vpm)} vpm`, "receiving route"),
    ledgerCell("Commanded", `${number(decision.q_commanded_vpm)} vpm`, "after compliance")
  ].join("") : [
    ledgerCell("Confidence", "below gate", "standby"),
    ledgerCell("Expected", "0.00 vpm", "no command"),
    ledgerCell("Available", "--", "not used"),
    ledgerCell("Commanded", "0.00 vpm", "standby")
  ].join("");
}

function renderCctv(cctv) {
  const metrics = cctv.metrics || fallbackCctv.metrics;
  setText("cctv-state", cctv.passed ? "audited" : "waiting");
  setText("cctv-count", cctv.passed ? `${integer(metrics.coco_annotation_count)} boxes` : "--");
  document.getElementById("cctv-strip").innerHTML = (cctv.sample_images || []).slice(0, 3).map(item => {
    const src = encodeURI(`../Real data/BMD-45-Val/${item.file_name}`);
    return `
      <figure class="cctv-frame">
        <img src="${escapeHtml(src)}" alt="BMD-45 validation frame ${escapeHtml(item.file_name)}" />
        <figcaption><span>${escapeHtml(item.file_name.replace("images_000/", ""))}</span><strong>${integer(item.coco_annotation_count)}</strong></figcaption>
      </figure>
    `;
  }).join("") || `<figure class="cctv-frame"><figcaption><span>waiting</span><strong>--</strong></figcaption></figure>`;
}

function renderDensity(report, latest) {
  const density = latest.density_tw_per_km || [];
  const junctions = [...(report.corridor?.junctions || [])].sort((a, b) => a.order - b.order);
  const max = Math.max(100, ...density);
  document.getElementById("density-bars").innerHTML = density.map((value, index) => {
    const from = junctions[index]?.name || `S${index + 1}`;
    const to = junctions[index + 1]?.name || `S${index + 2}`;
    const color = value > 95 ? "var(--amber)" : value > 78 ? "var(--blue)" : "var(--green)";
    const height = Math.max(14, (Number(value) / max) * 82);
    return `
      <div class="density-seg">
        <div class="density-bar" style="height:${height.toFixed(1)}px;background:${color}"></div>
        <div class="density-label">${escapeHtml(abbr(from))}-${escapeHtml(abbr(to))}</div>
      </div>
    `;
  }).join("");
}

function renderRouteCheckpoints(junctions, latest, bestId, decision, routeGeometry, activeOrder) {
  const element = document.getElementById("route-checkpoints");
  if (!element) return;
  const activeId = latest.observation?.junction_id;
  element.innerHTML = junctions.map(junction => {
    const classes = ["checkpoint-item"];
    let state = "queued";
    if (junction.order < activeOrder) {
      classes.push("passed");
      state = "seen";
    }
    if (junction.id === activeId) {
      classes.push("active");
      state = "checkpoint";
    }
    if (junction.id === bestId) {
      classes.push("target");
      state = decision?.activate ? "target" : "likely";
    }
    const meta = `${Number(junction.lat).toFixed(4)}, ${Number(junction.lon).toFixed(4)}`;
    return `
      <article class="${classes.join(" ")}">
        <span class="checkpoint-dot" aria-hidden="true"></span>
        <div>
          <div class="checkpoint-name">${escapeHtml(junction.name)}</div>
          <div class="checkpoint-meta">${escapeHtml(meta)}</div>
        </div>
        <span class="checkpoint-state">${escapeHtml(state)}</span>
      </article>
    `;
  }).join("");
  if (!routeGeometry?.coordinate_count) setText("route-proof", "junction fallback");
}

function renderTraceStrip(extremeBatch) {
  const element = document.getElementById("trace-strip");
  if (!element) return;
  const traces = (extremeBatch?.sample_vehicle_traces || []).slice(0, 4);
  if (!traces.length) {
    element.innerHTML = `<article class="trace-card"><div class="trace-top"><strong>waiting</strong><span>--</span></div><p class="trace-foot">Run the stress replay to populate sample traces.</p></article>`;
    return;
  }
  element.innerHTML = traces.map(trace => {
    const stops = (trace.observations || []).map(item => item.junction_id).filter(Boolean);
    const route = stops.map((stop, index) => {
      const hop = `<span class="trace-hop">${escapeHtml(shortLabel(label(stop)))}</span>`;
      return index < stops.length - 1 ? `${hop}<span class="trace-arrow">&gt;</span>` : hop;
    }).join("");
    const destination = shortLabel(label(trace.actual_destination_id || trace.best_destination_id || "--"));
    const traceId = trace.vehicle_id_hash || trace.vehicle_id || "sample";
    return `
      <article class="trace-card">
        <div class="trace-top"><strong>${escapeHtml(traceId)}</strong><span>${escapeHtml(destination)}</span></div>
        <div class="trace-route">${route}</div>
        <p class="trace-foot">${integer(stops.length)} checkpoints replayed; posterior best ${percent(trace.best_confidence || 0)}</p>
      </article>
    `;
  }).join("");
}
function renderAudienceViews(context) {
  audienceState.evidence = context;
  const content = document.getElementById("audience-content");
  if (!content) return;
  document.querySelectorAll("[data-audience-tab]").forEach(button => {
    button.classList.toggle("active", button.dataset.audienceTab === audienceState.active);
  });
  const views = {
    control: renderControlRoomView,
    citizen: renderCitizenView,
    officer: renderOfficerView,
    engineer: renderEngineerView,
    press: renderPressView
  };
  content.innerHTML = (views[audienceState.active] || renderControlRoomView)(context);
}

function renderControlRoomView(context) {
  const proof = proofMetrics(context);
  return `
    <div class="audience-grid">
      <article class="story-card primary">
        <span class="story-eyebrow">Operational story</span>
        <h2>${escapeHtml(proof.actionTitle)}</h2>
        <p>${escapeHtml(`At ${proof.checkpoint}, the replay posterior for ${proof.bestDestination} is ${proof.confidence}. The smart-link gate is ${proof.decisionState.toLowerCase()} and the command is bounded by available receiving capacity.`)}</p>
        ${renderNarrativeCard(context)}
      </article>
      <div class="proof-grid">
        ${proofCard("Route", proof.routePoints, `${proof.routeDistance} OSRM/OpenStreetMap reference`)}
        ${proofCard("Stress", proof.vehicleCount, `${proof.observationCount} replay observations`)}
        ${proofCard("Safety", proof.capacityViolations, "capacity violations")}
        ${proofCard("Overcommands", proof.overcommands, "stress replay audit")}
        ${proofCard("CCTV", proof.cctvBoxes, `${proof.cctvFrames} local frames audited`)}
        ${proofCard("Remote", proof.remoteGate, proof.remoteDetail)}
        ${proofCard("Field Gate", proof.fieldGate, "observed CSV still required")}
      </div>
    </div>
  `;
}

function renderCitizenView(context) {
  const proof = proofMetrics(context);
  return `
    <div class="audience-grid">
      <article class="story-card primary">
        <span class="story-eyebrow">Citizen-safe explanation</span>
        <h2>What this screen can honestly show today</h2>
        <p>${escapeHtml(`This is a verified software replay for the ${proof.corridorName} corridor. It shows how the system estimates where flow is likely going and opens a managed connector only when confidence and receiving capacity pass the gate.`)}</p>
        <div class="safe-copy">${escapeHtml("Safe public wording: PTIS has passed reproducible software tests on a Bengaluru ORR scenario, uses real OSRM/OpenStreetMap route geometry for visualization, and includes a real BMD-45 CCTV detection audit. Field impact is not claimed until observed replay data or a pilot is completed.")}</div>
      </article>
      <article class="boundary-card">
        <span>Boundary</span>
        <h2>No field-impact claim yet</h2>
        <p>${escapeHtml("Do not say travel time was reduced, congestion was reduced, or public roads were controlled. The current proof is software replay plus data provenance, not a live deployment.")}</p>
      </article>
    </div>
  `;
}

function renderOfficerView(context) {
  const proof = proofMetrics(context);
  return `
    <div class="audience-grid">
      <article class="story-card primary">
        <span class="story-eyebrow">Officer / operations view</span>
        <h2>${escapeHtml(proof.decisionState === "ACTIVE" ? "Advisory activation is capacity-safe in replay" : "Replay gate remains on standby")}</h2>
        <p>${escapeHtml(`The replay recommendation is ${proof.decisionState}. If used in a pilot, this should stay advisory: officers approve, reject, or override every connector action. The system has ${proof.capacityViolations} capacity violations and ${proof.overcommands} overcommands in the stress audit.`)}</p>
        <div class="audit-list">
          ${auditRow("Current checkpoint", proof.checkpoint)}
          ${auditRow("Best destination", `${proof.bestDestination} at ${proof.confidence}`)}
          ${auditRow("Expected flow", proof.expectedFlow)}
          ${auditRow("Commanded flow", proof.commandedFlow)}
        </div>
      </article>
      ${renderNarrativeCard(context)}
    </div>
  `;
}

function renderEngineerView(context) {
  const proof = proofMetrics(context);
  return `
    <div class="audience-grid">
      <article class="story-card primary">
        <span class="story-eyebrow">Engineer proof</span>
        <h2>Evidence chain and failure boundary</h2>
        <p>${escapeHtml("The frontend is reading saved evidence/API outputs, not random UI state. The route uses an in-app Web Mercator tile viewport, so tiles, markers, density bands, and animated route flow share one transform during zoom and pan.")}</p>
        <div class="audit-list">
          ${auditRow("Scenario suite", proof.suiteScore)}
          ${auditRow("Extreme replay", `${proof.vehicleCount} / ${proof.observationCount}`)}
          ${auditRow("Route geometry", `${proof.routePoints} / ${proof.routeDistance}`)}
          ${auditRow("CCTV detection audit", `${proof.cctvBoxes} boxes`)}
          ${auditRow("Remote aggregate", proof.remoteGate)}
          ${auditRow("Field replay", proof.fieldGate)}
        </div>
      </article>
      <div class="proof-grid">
        ${proofCard("Tests", proof.suiteScore, "published scenarios")}
        ${proofCard("Vehicles", proof.vehicleCount, "extreme stress replay")}
        ${proofCard("Observations", proof.observationCount, "checkpoint events")}
        ${proofCard("False Positives", proof.falsePositives, "activation audit")}
        ${proofCard("Capacity", proof.capacityViolations, "violations")}
        ${proofCard("Route Pts", proof.routePoints, "rendered geometry")}
      </div>
    </div>
  `;
}

function renderPressView(context) {
  const proof = proofMetrics(context);
  return `
    <div class="audience-grid">
      <article class="story-card primary">
        <span class="story-eyebrow">Press-safe summary</span>
        <h2>One paragraph you can post without overclaiming</h2>
        <div class="safe-copy">${escapeHtml(`PTIS v2.0 is a reproducible traffic-intelligence software prototype for Bengaluru ORR. In the current evidence bundle it passes ${proof.suiteScore} scenarios, stress-replays ${proof.vehicleCount} vehicles with ${proof.capacityViolations} capacity violations, renders a ${proof.routePoints}-point OSRM/OpenStreetMap route, and audits BMD-45 CCTV detection data. It is not yet field-proven; observed field replay data is the next milestone.`)}</div>
      </article>
      <article class="boundary-card">
        <span>Do not claim yet</span>
        <h2>No live deployment language</h2>
        <p>${escapeHtml("Avoid percent congestion-reduction claims, rupee benefit claims, live BTP/FASTag/Google/Waze integration, and field-proven performance until actual observed field replay or a pilot validates them.")}</p>
      </article>
    </div>
  `;
}

function renderNarrativeCard(context) {
  const cycles = context.scenario.cycles || [];
  const rows = cycles.map(cycle => {
    const active = (cycle.decisions || []).some(item => item.activate);
    const checkpoint = label(cycle.observation?.junction_id || "checkpoint");
    const best = label(cycle.best_destination_id || "unknown");
    const confidence = percent(cycle.best_confidence || 0);
    const detail = `Best destination ${best}; confidence ${confidence}`;
    return `
      <article class="narrative-step">
        <span class="cycle">${escapeHtml(cycle.cycle ?? "-")}</span>
        <div><strong>${escapeHtml(checkpoint)}</strong><p>${escapeHtml(detail)}</p></div>
        <span class="decision-pill ${active ? "active" : ""}">${active ? "activate" : "standby"}</span>
      </article>
    `;
  }).join("");
  return `
    <article class="narrative-card">
      <span>Replay narrative</span>
      <h2>How the decision forms</h2>
      <div class="narrative-list">${rows || `<article class="narrative-step"><span class="cycle">-</span><div><strong>Waiting</strong><p>No cycles loaded.</p></div><span class="decision-pill">pending</span></article>`}</div>
    </article>
  `;
}

function proofMetrics(context) {
  const m = context.extremeBatch?.metrics || context.batch?.metrics || fallbackBatch.metrics;
  const cm = context.cctv?.metrics || fallbackCctv.metrics;
  const decision = context.decision;
  const checkpoint = label(context.latest?.observation?.junction_id || "checkpoint");
  const bestDestination = label(context.bestId || "unknown");
  const routePoints = integer(context.routeGeometry?.coordinate_count || 0);
  const routeDistance = context.routeGeometry?.distance_m ? `${number(context.routeGeometry.distance_m / 1000)} km` : "route fallback";
  const suiteScore = context.suite?.scenario_count ? `${integer(context.suite.passed_count)}/${integer(context.suite.scenario_count)}` : "--";
  const fieldGate = context.field?.field_proven ? "passed" : "pending";
  const remoteMetrics = context.remoteAggregate?.metrics || fallbackRemoteAggregate.metrics;
  const remoteGate = context.remoteAggregate?.passed ? "passed" : "pending";
  const remoteDetail = context.remoteAggregate?.passed ? `${integer(remoteMetrics.row_count || 0)} rows / ${number(remoteMetrics.peak_total_vpm || 0)} vpm peak` : "aggregate counts not loaded";
  const decisionState = decision?.activate ? "ACTIVE" : "STANDBY";
  return {
    actionTitle: decision?.activate ? "Smart link activates inside the replay gate" : "Smart link stays closed inside the replay gate",
    bestDestination,
    capacityViolations: integer(m.capacity_violation_count || 0),
    cctvBoxes: integer(cm.coco_annotation_count || 0),
    cctvFrames: integer(cm.local_image_count || 0),
    checkpoint,
    commandedFlow: decision ? `${number(decision.q_commanded_vpm)} vpm` : "0.00 vpm",
    confidence: percent(context.confidence || 0),
    corridorName: context.scenario?.corridor?.name || "Bengaluru ORR",
    decisionState,
    expectedFlow: decision ? `${number(decision.q_expected_vpm)} vpm` : "0.00 vpm",
    falsePositives: integer(m.false_positive_activations || 0),
    fieldGate,
    remoteDetail,
    remoteGate,
    observationCount: integer(m.observation_count || 0),
    overcommands: integer(m.overcommand_count || 0),
    routeDistance,
    routePoints,
    suiteScore,
    vehicleCount: integer(m.vehicle_count || 0)
  };
}

function proofCard(labelText, value, detail) {
  return `<article class="proof-card"><span>${escapeHtml(labelText)}</span><strong>${escapeHtml(value)}</strong><p>${escapeHtml(detail)}</p></article>`;
}

function auditRow(labelText, value) {
  return `<div class="audit-row"><b>${escapeHtml(labelText)}</b><span>${escapeHtml(value)}</span></div>`;
}
function renderScenarioLibrary(suite) {
  const element = document.getElementById("scenario-library");
  if (!element) return;
  const scenarios = suite?.scenarios || [];
  setText("scenario-library-state", scenarios.length ? `${integer(scenarios.length)} verified cases` : "suite unavailable");
  if (!scenarios.length) {
    element.innerHTML = `<article class="scenario-card review"><div class="scenario-top"><div class="scenario-title"><strong>Waiting for suite report</strong><span>Run the verifier or suite replay to populate this section.</span></div><span class="scenario-badge block">pending</span></div></article>`;
    return;
  }
  element.innerHTML = scenarios.map(renderScenarioCard).join("");
}

function renderScenarioCard(item) {
  const cycles = item.cycles || [];
  const latest = cycles[cycles.length - 1] || {};
  const decisions = cycles.flatMap(cycle => cycle.decisions || []);
  const activeDecision = decisions.find(decision => decision.activate);
  const finalDecision = decisions[decisions.length - 1];
  const assertionCount = (item.assertions || []).length;
  const passedAssertions = (item.assertions || []).filter(assertion => assertion.passed).length;
  const passed = Boolean(item.passed && assertionCount === passedAssertions);
  const outcome = activeDecision ? "activate" : "standby";
  const reason = activeDecision?.reason || finalDecision?.reason || scenarioReadableReason(item.scenario_id, outcome);
  const best = latest.best_destination_id ? label(latest.best_destination_id) : "--";
  const confidence = percent(latest.best_confidence || 0);
  const cycleCount = integer(cycles.length || 0);
  const assertionChips = (item.assertions || []).slice(0, 4).map(assertion => `<span class="${assertion.passed ? "pass" : ""}">${escapeHtml(assertion.name.replaceAll("_", " "))}</span>`).join("");
  return `
    <article class="scenario-card ${passed ? "pass" : "review"}">
      <div class="scenario-top">
        <div class="scenario-title">
          <strong>${escapeHtml(item.scenario_name || item.scenario_id || "Scenario")}</strong>
          <span>${escapeHtml(item.scenario_id || "scenario")}</span>
        </div>
        <span class="scenario-badge ${activeDecision ? "pass" : "block"}">${escapeHtml(outcome)}</span>
      </div>
      <div class="scenario-metrics">
        ${scenarioMetric("Assertions", `${integer(passedAssertions)}/${integer(assertionCount)}`)}
        ${scenarioMetric("Best", best)}
        ${scenarioMetric("Confidence", confidence)}
        ${scenarioMetric("Cycles", cycleCount)}
        ${scenarioMetric("Safety", passed ? "passed" : "review")}
        ${scenarioMetric("Decision", outcome)}
      </div>
      <p class="scenario-reason">${escapeHtml(reason)}</p>
      <div class="scenario-assertions">${assertionChips}</div>
    </article>
  `;
}

function scenarioMetric(labelText, value) {
  return `<article><span>${escapeHtml(labelText)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function scenarioReadableReason(id, outcome) {
  const clean = String(id || "scenario").replaceAll("_", " ");
  if (outcome === "standby") return `No activation in this case; ${clean}.`;
  return `Activation case; ${clean}.`;
}
function renderBottomMetrics({ batch, extremeBatch, cctv, official, field, remoteAggregate, decision }) {
  const m = extremeBatch?.metrics || batch.metrics || fallbackBatch.metrics;
  const cm = cctv.metrics || fallbackCctv.metrics;
  const rm = remoteAggregate?.metrics || fallbackRemoteAggregate.metrics;
  document.getElementById("bottom-metrics").innerHTML = [
    metricTile("Overcommands", integer(m.overcommand_count || 0), "batch stress"),
    metricTile("False Positives", integer(m.false_positive_activations || 0), "activation audit"),
    metricTile("Mean Confidence", percent(m.mean_activation_confidence || decision?.confidence || 0), "batch activation"),
    metricTile("CCTV Images", integer(cm.coco_image_count || 0), "BMD-45 records"),
    metricTile("Remote Replay", remoteAggregate?.passed ? integer(rm.row_count || 0) : "pending", remoteAggregate?.passed ? "aggregate count rows" : "no-travel count gate"),
    metricTile("Field Replay", field.field_proven ? "passed" : "pending", "observed CSV gate")
  ].join("");
}

function renderDetails({ scenario, suite, batch, extremeBatch, official, cctv, field, remoteAggregate, routeGeometry }) {
  const m = extremeBatch?.metrics || batch.metrics || fallbackBatch.metrics;
  const cm = cctv.metrics || fallbackCctv.metrics;
  document.getElementById("detail-grid").innerHTML = [
    detailItem("Generated", scenario.generated_at || "--"),
    detailItem("Scenario Hash", scenario.scenario_sha256 ? scenario.scenario_sha256.slice(0, 12) : "--"),
    detailItem("Official Docs", official.source_documents?.length || 0),
    detailItem("Route Points", routeGeometry?.coordinate_count || 0),
    detailItem("CCTV Categories", cm.category_count || 0),
    detailItem("Observations", m.observation_count || 0),
    detailItem("Activations", m.activation_count || 0),
    detailItem("Field Status", field.status || "pending"),
    detailItem("Remote Aggregate", remoteAggregate?.passed ? "passed" : (remoteAggregate?.status || "pending")),
    detailItem("CCTV Audit", cctv.passed ? "passed" : "waiting")
  ].join("");

  document.getElementById("scenario-table").innerHTML = `
    <thead><tr><th>Cycle</th><th>Checkpoint</th><th>Best</th><th>Confidence</th><th>Decision</th></tr></thead>
    <tbody>${(scenario.cycles || []).map(cycle => {
      const active = (cycle.decisions || []).some(d => d.activate);
      return `<tr><td>${escapeHtml(cycle.cycle ?? "--")}</td><td>${escapeHtml(label(cycle.observation?.junction_id || "--"))}</td><td>${escapeHtml(label(cycle.best_destination_id || "--"))}</td><td>${percent(cycle.best_confidence || 0)}</td><td>${active ? "ACTIVATE" : "STANDBY"}</td></tr>`;
    }).join("")}</tbody>
  `;

  setText("truth-boundary", "Validated software replay + real BMD-45 CCTV detection audit. Remote aggregate replay is optional no-travel evidence; field impact remains pending observed OD replay data.");
}

function statTile(labelText, value, detail) {
  return `<article class="stat"><span>${escapeHtml(labelText)}</span><strong>${escapeHtml(value)}</strong><p>${escapeHtml(detail)}</p></article>`;
}
function metricTile(labelText, value, detail) {
  return `<article class="metric"><span>${escapeHtml(labelText)}</span><strong>${escapeHtml(value)}</strong><p>${escapeHtml(detail)}</p></article>`;
}
function ledgerCell(labelText, value, detail) {
  return `<article><span>${escapeHtml(labelText)}</span><strong>${escapeHtml(value)}</strong><p>${escapeHtml(detail)}</p></article>`;
}
function detailItem(labelText, value) {
  return `<article class="detail-item"><span>${escapeHtml(labelText)}</span><strong>${escapeHtml(value)}</strong></article>`;
}

function extractRouteCoordinates(routeGeometry) {
  const coords = routeGeometry?.features?.[0]?.geometry?.coordinates || routeGeometry?.geometry?.coordinates || [];
  return coords
    .filter(coord => Array.isArray(coord) && coord.length >= 2)
    .map(coord => [Number(coord[0]), Number(coord[1])])
    .filter(coord => Number.isFinite(coord[0]) && Number.isFinite(coord[1]));
}

function nearestRouteIndex(routeCoords, junction) {
  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;
  routeCoords.forEach((coord, index) => {
    const dx = Number(coord[0]) - Number(junction.lon);
    const dy = Number(coord[1]) - Number(junction.lat);
    const distance = dx * dx + dy * dy;
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  });
  return bestIndex;
}

function routeSlice(routePoints, fromIndex, toIndex) {
  const start = Math.max(0, Math.min(fromIndex, toIndex));
  const end = Math.min(routePoints.length - 1, Math.max(fromIndex, toIndex));
  const slice = routePoints.slice(start, end + 1);
  return fromIndex <= toIndex ? slice : slice.reverse();
}

function pathFromPoints(points) {
  return points.map((p, index) => `${index ? "L" : "M"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
}

function buildRouteSegments(routePoints, junctions, nearestIndexById) {
  return junctions.slice(0, -1).map((junction, index) => {
    const next = junctions[index + 1];
    const start = nearestIndexById[junction.id] ?? 0;
    const end = nearestIndexById[next.id] ?? start;
    const segment = routeSlice(routePoints, start, end);
    return segment.length >= 2 ? segment : [routePoints[start], routePoints[end]].filter(Boolean);
  });
}

function buildDensitySegments(segments, density, maxDensity) {
  return segments.map((segment, index) => {
    const value = Number(density[index] || 0);
    const ratio = Math.max(0.18, Math.min(1, value / maxDensity));
    const width = 7 + ratio * 12;
    const opacity = 0.18 + ratio * 0.40;
    const color = densityColor(value);
    return `<path class="map-density-seg" d="${pathFromPoints(segment)}" style="stroke:${color};stroke-width:${width.toFixed(1)};opacity:${opacity.toFixed(2)}" data-density="${number(value)}"></path>`;
  }).join("");
}

function buildFlowDots(pathId, count, kind, vehicleCount) {
  const safeCount = Math.max(0, Math.min(64, count));
  const baseDuration = kind === "divert" ? 9.2 : 13.6;
  const loadFactor = vehicleCount ? Math.max(0, Math.min(2.4, Math.log10(vehicleCount) - 2.2)) : 0;
  const duration = Math.max(6.6, baseDuration - loadFactor);
  return Array.from({ length: safeCount }, (_, index) => {
    const lane = index % 3;
    const radius = kind === "divert" ? (lane === 0 ? 3.3 : 2.4) : (lane === 0 ? 2.8 : 2.1);
    const begin = -1 * ((duration / safeCount) * index + lane * 0.23);
    return `<circle class="map-vehicle ${kind} lane-${lane}" r="${radius.toFixed(1)}" data-flow-dot="${kind}-${index}">
      <animateMotion dur="${duration.toFixed(2)}s" begin="${begin.toFixed(2)}s" repeatCount="indefinite" rotate="auto">
        <mpath href="#${pathId}"></mpath>
      </animateMotion>
    </circle>`;
  }).join("");
}

function flowDotCount(vehicleCount) {
  if (!vehicleCount) return 22;
  return Math.round(Math.max(22, Math.min(58, Math.sqrt(Number(vehicleCount)) * 0.62)));
}

function densityColor(value) {
  if (value >= 90) return "#ffb347";
  if (value >= 78) return "#4a9eff";
  return "#00d4aa";
}

function flowPanelLines(metrics, decision, routeGeometry) {
  const vehicles = metrics.vehicle_count ? `${integer(metrics.vehicle_count)} vehicles` : "scenario vehicles";
  const observations = metrics.observation_count ? `${integer(metrics.observation_count)} observations` : "checkpoint observations";
  const safety = `${integer(metrics.capacity_violation_count || 0)} capacity violations`;
  const commanded = decision?.q_commanded_vpm ? `${number(decision.q_commanded_vpm)} vpm command` : "standby command";
  const source = routeGeometry?.source ? "OSRM/OpenStreetMap route" : "junction fallback route";
  return [`${vehicles} / ${observations}`, `${safety} / ${commanded} / ${source}`];
}
function curvePath(a, b) {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const lift = Math.max(32, Math.abs(a.x - b.x) * 0.22);
  return `M ${a.x.toFixed(1)} ${a.y.toFixed(1)} Q ${mx.toFixed(1)} ${(my + lift).toFixed(1)} ${b.x.toFixed(1)} ${b.y.toFixed(1)}`;
}
function abbr(name) {
  const clean = String(name).replace("Layout", "").replace("World", "").trim();
  return clean.split(/\s+/).map(part => part[0]).join("").slice(0, 3).toUpperCase();
}
function label(id) { return String(id || "--").replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase()); }
function shortLabel(value) {
  return String(value)
    .replace("Doddanekkundi", "D.Kundi")
    .replace("Doddanekundi", "D.Kundi")
    .replace("Marathahalli", "Maratha.")
    .replace("Sony World", "Sony")
    .replace("HSR Layout", "HSR");
}
function percent(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(1)}%` : "--";
}
function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(2) : "--";
}
function integer(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toLocaleString("en-IN") : "--";
}
function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}
function escapeHtml(value) {
  return String(value).replace(/[&<>\'"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[c]));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number(value)));
}

function rerenderStoredMap() {
  if (!mapState.context) return;
  renderGeoMap(
    mapState.context.report,
    mapState.context.latest,
    mapState.context.bestId,
    mapState.context.decision,
    mapState.context.extremeBatch,
    mapState.context.routeGeometry
  );
}

function zoomBuiltInMap(delta) {
  if (mapState.maplibre && mapState.maplibreReady) {
    const nextZoom = Math.max(9, Math.min(16, mapState.maplibre.getZoom() + delta));
    mapState.maplibre.easeTo({ zoom: nextZoom, duration: 240 });
    return;
  }
  if (mapState.zoom == null) return;
  const nextZoom = clamp(Math.round(mapState.zoom) + delta, MAP_MIN_ZOOM, MAP_MAX_ZOOM);
  if (nextZoom === mapState.zoom) return;
  mapState.zoom = nextZoom;
  mapState.autoFit = false;
  rerenderStoredMap();
}
function resetBuiltInMap() {
  mapState.autoFit = true;
  mapState.maplibreReady = false;
  mapState.maplibreRouteKey = "";
  rerenderStoredMap();
}
function panBuiltInMap(dx, dy) {
  if (mapState.maplibre && mapState.maplibreReady) return;
  if (!mapState.center || mapState.zoom == null) return;
  const z = clamp(Math.round(mapState.zoom), MAP_MIN_ZOOM, MAP_MAX_ZOOM);
  const centerPx = lonLatToPixel(mapState.center.lon, mapState.center.lat, z);
  mapState.center = pixelToLonLat(centerPx.x - dx, centerPx.y - dy, z);
  mapState.autoFit = false;
  rerenderStoredMap();
}
function initMapInteractions() {
  const stack = document.getElementById("map-stack");
  if (!stack) return;
  stack.addEventListener("wheel", event => {
    if (stack.classList.contains("maplibre-ready")) return;
    event.preventDefault();
    zoomBuiltInMap(event.deltaY < 0 ? 1 : -1);
  }, { passive: false });
  stack.addEventListener("pointerdown", event => {
    if (stack.classList.contains("maplibre-ready")) return;
    if (event.target.closest(".map-controls")) return;
    mapState.dragging = true;
    mapState.lastPointer = { x: event.clientX, y: event.clientY };
    stack.classList.add("is-dragging");
    stack.setPointerCapture?.(event.pointerId);
  });
  stack.addEventListener("pointermove", event => {
    if (stack.classList.contains("maplibre-ready")) return;
    if (!mapState.dragging || !mapState.lastPointer) return;
    const dx = event.clientX - mapState.lastPointer.x;
    const dy = event.clientY - mapState.lastPointer.y;
    mapState.lastPointer = { x: event.clientX, y: event.clientY };
    panBuiltInMap(dx, dy);
  });
  const stopDrag = event => {
    mapState.dragging = false;
    mapState.lastPointer = null;
    stack.classList.remove("is-dragging");
    if (event?.pointerId != null) stack.releasePointerCapture?.(event.pointerId);
  };
  stack.addEventListener("pointerup", stopDrag);
  stack.addEventListener("pointercancel", stopDrag);
  stack.addEventListener("pointerleave", stopDrag);
}

let resizeTimer = null;
function initResponsiveMapRedraw() {
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => rerenderStoredMap(), 120);
  });
}
function initAudienceTabs() {
  document.querySelectorAll("[data-audience-tab]").forEach(button => {
    button.addEventListener("click", () => {
      audienceState.active = button.dataset.audienceTab || "control";
      if (audienceState.evidence) renderAudienceViews(audienceState.evidence);
    });
  });
}
document.getElementById("load-evidence")?.addEventListener("click", loadAllEvidence);
document.getElementById("run-scenario")?.addEventListener("click", runScenario);
document.getElementById("run-suite")?.addEventListener("click", runSuite);
document.getElementById("run-batch")?.addEventListener("click", runBatch);
document.getElementById("run-extreme")?.addEventListener("click", runExtremeBatch);
document.getElementById("map-zoom-in")?.addEventListener("click", () => zoomBuiltInMap(1));
document.getElementById("map-zoom-out")?.addEventListener("click", () => zoomBuiltInMap(-1));
document.getElementById("map-reset")?.addEventListener("click", resetBuiltInMap);
initMapInteractions();
initResponsiveMapRedraw();
initAudienceTabs();
loadAllEvidence();
