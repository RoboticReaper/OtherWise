const idOrder = (a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0;

/** Saved centers expand once through cached 768D nearest neighbors; searches do not. */
export function explorationSets(data, state = {}) {
  const catalog = data.byId;
  const saved = new Set((state.approved ?? []).filter(topic => catalog.has(topic?.id)).map(topic => topic.id));
  const explored = new Set((state.explored ?? []).filter(topic => catalog.has(topic?.id)).map(topic => topic.id));
  const nearby = new Set();
  for (const id of saved) {
    const neighbors = [...catalog.get(id).neighbors].sort((a, b) => a.distance - b.distance || idOrder(a, b)).slice(0, 10);
    for (const neighbor of neighbors) if (catalog.has(neighbor.id)) nearby.add(neighbor.id);
  }
  return {saved, nearby, explored, lit: new Set([...saved, ...nearby, ...explored])};
}
