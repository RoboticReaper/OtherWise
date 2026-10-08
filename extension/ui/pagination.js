export const PAGE_SIZE = 10;

export function paginate(items, page, pageSize = PAGE_SIZE) {
  const list = Array.isArray(items) ? items : [];
  const size = Number.isFinite(pageSize) && pageSize >= 1 ? Math.floor(pageSize) : PAGE_SIZE;
  const total = list.length;
  const pageCount = Math.max(1, Math.ceil(total / size));
  const current = Math.min(pageCount, Math.max(1, Number.isFinite(page) ? Math.floor(page) : 1));
  const offset = (current - 1) * size;
  return { items: list.slice(offset, offset + size), page: current, pageCount, total, start: total ? offset + 1 : 0, end: Math.min(total, offset + size) };
}

// Keep a topic selected across layouts; after dismissal, continue at its position.
export function recommendationCursor(items, selectedId, preferredIndex = 0) {
  const list = Array.isArray(items) ? items : [];
  if (!list.length) return {id: null, index: 0, topic: null, total: 0};
  const idOf = topic => topic.id || topic.topic;
  const found = list.findIndex(topic => idOf(topic) === selectedId);
  const fallback = Number.isFinite(preferredIndex) ? Math.floor(preferredIndex) : 0;
  const index = found >= 0 ? found : Math.max(0, Math.min(list.length - 1, fallback));
  return {id: idOf(list[index]), index, topic: list[index], total: list.length};
}
