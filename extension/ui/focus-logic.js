const K = 1000;
const idOrder = (a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
const distanceOrder = (a, b) => a.distance - b.distance || idOrder(a, b);
const knownDistance = value => Number.isFinite(value) && value >= 0 && value <= 1;

function stableAngle(seedId, topicId) {
  let hash = 2166136261;
  for (const character of JSON.stringify([seedId, topicId])) {
    hash = Math.imul(hash ^ character.codePointAt(0), 16777619) >>> 0;
  }
  return hash / 4294967296 * Math.PI * 2;
}

/** Local geometry uses fixed semantic radii and cached global directions only. */
export function projectFocus(data, seedId, recommendations = [], suppressed = []) {
  if (seedId === null || seedId === undefined || seedId === '') return {seedId: null, nodes: []};
  const seed = data?.byId?.get(seedId);
  if (!seed) throw new Error('Choose a topic from the catalog to open Focus.');
  const roles = new Map([[seedId, {distance: 0, isNeighbor: false, isRecommendation: false}]]);
  const neighbors = [...seed.neighbors].sort(distanceOrder).slice(0, 10);
  for (const neighbor of neighbors) {
    if (neighbor.id !== seedId && data.byId.has(neighbor.id) && knownDistance(neighbor.distance)) {
      roles.set(neighbor.id, {distance: neighbor.distance, isNeighbor: true, isRecommendation: false});
    }
  }
  const hidden = new Set(suppressed);
  const candidates = recommendations.filter(candidate => candidate && candidate.id !== seedId &&
    !hidden.has(candidate.id) && data.byId.has(candidate.id) && knownDistance(candidate.distance));
  for (const candidate of candidates.sort(distanceOrder)) {
    const existing = roles.get(candidate.id);
    if (existing) existing.isRecommendation = true;
    else roles.set(candidate.id, {distance: candidate.distance, isNeighbor: false, isRecommendation: true});
  }
  const nodes = [...roles].map(([id, role]) => {
    const topic = data.byId.get(id);
    const dx = topic.x - seed.x, dy = topic.y - seed.y;
    const angle = dx === 0 && dy === 0 ? stableAngle(seedId, id) : Math.atan2(dy, dx);
    const radius = K * role.distance;
    return {...topic, neighbors: [...topic.neighbors].sort(distanceOrder), ...role,
      x: id === seedId ? 0 : radius * Math.cos(angle), y: id === seedId ? 0 : radius * Math.sin(angle)};
  }).sort((a, b) => a.id === seedId ? -1 : b.id === seedId ? 1 : distanceOrder(a, b));
  return {seedId, nodes};
}
