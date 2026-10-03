const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const validId = value => typeof value === 'string' && value.length > 0;
const coordinate = value => typeof value === 'number' && Number.isFinite(value) && Math.abs(value) < 1e6;
const normalize = value => value.normalize('NFKC').toLocaleLowerCase().trim();
const invalid = () => { throw new Error('The Galaxy layout does not match the topic catalog.'); };

/** Join by canonical topic IDs; catalog text is the only text authority. */
export function prepareGalaxy(catalog, layout) {
  if (!Array.isArray(catalog) || !catalog.length || layout?.schema_version !== 1 ||
      !validId(layout.cache_key) || !layout.metadata || typeof layout.metadata !== 'object' ||
      !Array.isArray(layout.topics) || !Array.isArray(layout.domains)) invalid();
  const catalogById = new Map();
  for (const topic of catalog) {
    if (!validId(topic?.id) || !validId(topic.topic) || !validId(topic.domain) ||
        typeof topic.description !== 'string' || catalogById.has(topic.id)) invalid();
    catalogById.set(topic.id, topic);
  }
  if (layout.topics.length !== catalog.length) invalid();
  const domainIds = new Set(catalog.map(topic => topic.domain));
  const domains = new Map();
  for (const domain of layout.domains) {
    if (!domainIds.has(domain?.id) || domains.has(domain.id) || !coordinate(domain.x) || !coordinate(domain.y)) invalid();
    domains.set(domain.id, {...domain});
  }
  if (domains.size !== domainIds.size) invalid();
  const byId = new Map();
  const bounds = {minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity};
  for (const point of layout.topics) {
    if (!catalogById.has(point?.id) || byId.has(point.id) || !coordinate(point.x) || !coordinate(point.y) || !Array.isArray(point.neighbors)) invalid();
    const seen = new Set();
    const neighbors = point.neighbors.map(neighbor => {
      if (!catalogById.has(neighbor?.id) || neighbor.id === point.id || seen.has(neighbor.id) ||
          !Number.isFinite(neighbor.distance) || neighbor.distance < 0 || neighbor.distance > 1) invalid();
      seen.add(neighbor.id);
      return {id: neighbor.id, distance: neighbor.distance};
    }).sort((a, b) => a.distance - b.distance);
    const topic = catalogById.get(point.id);
    byId.set(point.id, {...topic, x: point.x, y: point.y, neighbors,
      searchTitle: normalize(topic.topic), searchText: normalize(`${topic.topic} ${topic.domain} ${topic.description}`)});
    bounds.minX = Math.min(bounds.minX, point.x); bounds.maxX = Math.max(bounds.maxX, point.x);
    bounds.minY = Math.min(bounds.minY, point.y); bounds.maxY = Math.max(bounds.maxY, point.y);
  }
  return {topics: [...byId.values()], byId, domains: [...domains.values()].sort((a, b) => a.id.localeCompare(b.id)), bounds, cacheKey: layout.cache_key};
}

export function topicsInDomain(data, domain = null) {
  return domain ? data.topics.filter(topic => topic.domain === domain) : data.topics;
}

export function searchTopics(data, query, domain = null, limit = 12) {
  const term = normalize(typeof query === 'string' ? query : '');
  if (!term) return [];
  const words = term.split(/\s+/);
  return topicsInDomain(data, domain).filter(topic => words.every(word => topic.searchText.includes(word)))
    .sort((a, b) => {
      const rank = topic => topic.searchTitle === term ? 0 : topic.searchTitle.startsWith(term) ? 1 : topic.searchTitle.includes(term) ? 2 : 3;
      return rank(a) - rank(b) || a.topic.localeCompare(b.topic);
    }).slice(0, limit);
}

export function defaultCamera(bounds) {
  return {x: (bounds.minX + bounds.maxX) / 2, y: (bounds.minY + bounds.maxY) / 2, zoom: 1};
}

export function clampCamera(camera, bounds) {
  const center = defaultCamera(bounds), span = Math.max(bounds.maxX - bounds.minX, bounds.maxY - bounds.minY, 1);
  return {
    x: clamp(Number.isFinite(camera?.x) ? camera.x : center.x, center.x - span * 2, center.x + span * 2),
    y: clamp(Number.isFinite(camera?.y) ? camera.y : center.y, center.y - span * 2, center.y + span * 2),
    zoom: clamp(Number.isFinite(camera?.zoom) ? camera.zoom : 1, .65, 20),
  };
}

export function restoreViewState(viewState, data, customIds = []) {
  const domain = data.domains.some(item => item.id === viewState?.domain) ? viewState.domain : null;
  return {
    query: typeof viewState?.query === 'string' ? viewState.query.slice(0, 200) : '', domain,
    selected: data.byId.has(viewState?.selected) || customIds.includes(viewState?.selected) ? viewState.selected : null,
    camera: clampCamera(viewState?.camera, data.bounds),
  };
}

export function cameraScale(camera, viewport, bounds) {
  return Math.max(Number.EPSILON, Math.min(viewport.width / Math.max(bounds.maxX - bounds.minX, 1), viewport.height / Math.max(bounds.maxY - bounds.minY, 1)) * .82) * camera.zoom;
}

export function worldToScreen(point, camera, viewport, bounds) {
  const scale = cameraScale(camera, viewport, bounds);
  return {x: viewport.width / 2 + (point.x - camera.x) * scale, y: viewport.height / 2 - (point.y - camera.y) * scale};
}

export function screenToWorld(point, camera, viewport, bounds) {
  const scale = cameraScale(camera, viewport, bounds);
  return {x: camera.x + (point.x - viewport.width / 2) / scale, y: camera.y - (point.y - viewport.height / 2) / scale};
}

export function zoomAt(camera, factor, pointer, viewport, bounds) {
  const anchor = screenToWorld(pointer, camera, viewport, bounds);
  const next = {...camera, zoom: clamp(camera.zoom * factor, .65, 20)};
  const shifted = screenToWorld(pointer, next, viewport, bounds);
  return clampCamera({...next, x: next.x + anchor.x - shifted.x, y: next.y + anchor.y - shifted.y}, bounds);
}

export function panCamera(camera, dx, dy, viewport, bounds) {
  const scale = cameraScale(camera, viewport, bounds);
  return clampCamera({...camera, x: camera.x - dx / scale, y: camera.y + dy / scale}, bounds);
}

export function hitTest(hits, pointer, radius = 14) {
  let best = null, nearest = radius;
  for (const point of hits) {
    const distance = Math.hypot(point.x - pointer.x, point.y - pointer.y);
    if (distance < nearest) { nearest = distance; best = point.id; }
  }
  return best;
}
